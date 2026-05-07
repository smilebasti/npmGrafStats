"""AbuseIPDB checker with SQLite WAL-mode cache (thread-safe)."""

import json
import logging
import os
import sqlite3
import threading
import time

import requests

from config import ABUSEIP_CACHE_DB, ABUSEIP_CACHE_JSON, CACHE_TTL_HOURS, DATA_DIR

logger = logging.getLogger(__name__)

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
    def __init__(self, api_key: str | None):
        self._api_key = api_key
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()
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
        cutoff = time.time() - CACHE_TTL_HOURS * 3600
        if self._conn:
            self._conn.execute("DELETE FROM abuse_cache WHERE fetched_at < ?", (cutoff,))
            self._conn.commit()
            logger.info("Cleaned up expired abuse cache entries (older than %dh)", CACHE_TTL_HOURS)

    @property
    def enabled(self) -> bool:
        return self._api_key is not None

    def check(self, ip: str) -> tuple[int, int]:
        """Returns (confidence_score, total_reports). (0, 0) if unavailable."""
        if not self._api_key or not self._conn:
            return 0, 0

        cutoff = time.time() - CACHE_TTL_HOURS * 3600

        with self._lock:
            row = self._conn.execute(
                "SELECT confidence_score, total_reports FROM abuse_cache WHERE ip = ? AND fetched_at >= ?",
                (ip, cutoff),
            ).fetchone()
        if row:
            logger.debug("AbuseIPDB cache HIT for %s", ip)
            return row[0], row[1]

        # Cache miss - fetch from API (outside lock to avoid blocking other threads)
        logger.debug("AbuseIPDB cache MISS for %s", ip)
        try:
            resp = requests.get(
                "https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": ip, "maxAgeInDays": "90"},
                headers={"Accept": "application/json", "Key": self._api_key},
                timeout=10,
            )
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