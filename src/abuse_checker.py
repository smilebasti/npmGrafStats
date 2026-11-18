"""AbuseIPDB checker with SQLite WAL-mode cache (thread-safe)."""

import json
import logging
import os
import sqlite3
import threading
import time

import requests

from config import ABUSEIP_CACHE_DB, ABUSEIP_CACHE_JSON, DEFAULT_CACHE_TTL_HOURS, DATA_DIR

logger = logging.getLogger(__name__)

# How often expired cache entries are purged while running (seconds)
CLEANUP_INTERVAL = 3600
# Pause after HTTP 429 when AbuseIPDB sends no usable reset header (seconds)
DEFAULT_RATE_LIMIT_PAUSE = 3600

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS abuse_cache (
    ip TEXT PRIMARY KEY,
    confidence_score INTEGER,
    total_reports INTEGER,
    data_json TEXT,
    fetched_at REAL
)
"""


class AbuseChecker:
    def __init__(self, api_key: str | None, cache_ttl_hours: float = DEFAULT_CACHE_TTL_HOURS):
        self._api_key = api_key
        self._ttl_hours = cache_ttl_hours
        self._ttl_seconds = cache_ttl_hours * 3600
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()
        self._last_cleanup = 0.0
        self._blocked_until = 0.0
        if not api_key:
            logger.info("AbuseIPDB disabled (no API key)")
            return
        self._init_db()

    def _init_db(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._conn = sqlite3.connect(ABUSEIP_CACHE_DB, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()
        self._migrate_json_cache()
        self._cleanup_expired()

    def _migrate_json_cache(self):
        """Migrate existing JSON cache to SQLite on first run."""
        if not os.path.isfile(ABUSEIP_CACHE_JSON):
            return
        try:
            with open(ABUSEIP_CACHE_JSON, "r") as f:
                data = json.load(f)
            count = 0
            for ip, entry in data.items():
                ts = entry.get("timestamp", 0)
                d = entry.get("data", {})
                self._conn.execute(
                    "INSERT OR IGNORE INTO abuse_cache (ip, confidence_score, total_reports, data_json, fetched_at) VALUES (?, ?, ?, ?, ?)",
                    (ip, d.get("abuseConfidenceScore", 0), d.get("totalReports", 0), json.dumps(d), ts),
                )
                count += 1
            self._conn.commit()
            # Rename old file
            os.rename(ABUSEIP_CACHE_JSON, ABUSEIP_CACHE_JSON + ".migrated")
            logger.info("Migrated %d entries from JSON cache to SQLite", count)
        except Exception as e:
            logger.warning("JSON cache migration failed: %s", e)

    def _cleanup_expired(self):
        """Delete cache entries older than the TTL. Safe to call from any thread."""
        if not self._conn:
            return
        cutoff = time.time() - self._ttl_seconds
        with self._lock:
            cur = self._conn.execute("DELETE FROM abuse_cache WHERE fetched_at < ?", (cutoff,))
            self._conn.commit()
            self._last_cleanup = time.time()
        logger.info("Cleaned up %d expired abuse cache entries (older than %gh)", cur.rowcount, self._ttl_hours)

    def _maybe_cleanup(self):
        if time.time() - self._last_cleanup >= CLEANUP_INTERVAL:
            self._cleanup_expired()

    @staticmethod
    def _rate_limit_pause(resp: requests.Response) -> float:
        """Seconds to wait after a 429, based on AbuseIPDB's headers."""
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), 1.0)
            except ValueError:
                pass
        reset = resp.headers.get("X-RateLimit-Reset")
        if reset:
            try:
                return max(float(reset) - time.time(), 1.0)
            except ValueError:
                pass
        return DEFAULT_RATE_LIMIT_PAUSE

    @property
    def enabled(self) -> bool:
        return self._api_key is not None

    def check(self, ip: str) -> tuple[int, int]:
        """Returns (confidence_score, total_reports). (0, 0) if unavailable."""
        if not self._api_key or not self._conn:
            return 0, 0

        self._maybe_cleanup()
        cutoff = time.time() - self._ttl_seconds

        with self._lock:
            row = self._conn.execute(
                "SELECT confidence_score, total_reports FROM abuse_cache WHERE ip = ? AND fetched_at >= ?",
                (ip, cutoff),
            ).fetchone()
        if row:
            logger.debug("AbuseIPDB cache HIT for %s", ip)
            return row[0], row[1]

        # Rate limit reached earlier: don't call the API until it resets
        if time.time() < self._blocked_until:
            logger.debug("AbuseIPDB rate limited, skipping lookup for %s", ip)
            return 0, 0

        # Cache miss - fetch from API (outside lock to avoid blocking other threads)
        logger.debug("AbuseIPDB cache MISS for %s", ip)
        try:
            resp = requests.get(
                "https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": ip, "maxAgeInDays": "90"},
                headers={"Accept": "application/json", "Key": self._api_key},
                timeout=10,
            )
            if resp.status_code == 429:
                pause = self._rate_limit_pause(resp)
                with self._lock:
                    already_blocked = time.time() < self._blocked_until
                    self._blocked_until = max(self._blocked_until, time.time() + pause)
                if not already_blocked:
                    logger.warning("AbuseIPDB rate limit reached, pausing lookups for %.0f min "
                                   "(abuse scores are written as 0 meanwhile)", pause / 60)
                return 0, 0
            resp.raise_for_status()
            api_data = resp.json().get("data", {})
            cs = api_data.get("abuseConfidenceScore", 0)
            tr = api_data.get("totalReports", 0)
            with self._lock:
                self._conn.execute(
                    "INSERT OR REPLACE INTO abuse_cache (ip, confidence_score, total_reports, data_json, fetched_at) VALUES (?, ?, ?, ?, ?)",
                    (ip, cs, tr, json.dumps(api_data), time.time()),
                )
                self._conn.commit()
            return cs, tr
        except Exception as e:
            logger.warning("AbuseIPDB API error for %s: %s", ip, e)
            return 0, 0

    def close(self):
        if self._conn:
            self._conn.close()
