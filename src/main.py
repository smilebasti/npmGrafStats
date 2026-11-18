#!/usr/bin/env python3
"""npmGrafStats (NPMplus) - Python rewrite. Single entrypoint."""

import glob
import logging
import os
import signal
import sys
import threading


# Set at build time from the git tag (Docker build-arg APP_VERSION)
VERSION = os.getenv("APP_VERSION", "dev")

# Interval (seconds) for picking up log files of newly created hosts
RESCAN_INTERVAL = 60

# NPMplus does not log an upstream/target IP. Use a dash placeholder so the
# Grafana dashboards that read the "Target" tag still get a valid value.
TARGET_PLACEHOLDER = "-"

_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("npmGrafStats")

VERBOSE = os.getenv("VERBOSE_LOGGING", "FALSE").upper() == "TRUE"

stop_event = threading.Event()


def _is_healthcheck(user_agent: str) -> bool:
    return "NPMplus/healthcheck" in user_agent


# Set once startup is complete; before that a stop signal exits immediately
_started = threading.Event()


def _shutdown(signum, frame):
    logger.info("Received signal %d, shutting down...", signum)
    stop_event.set()
    if not _started.is_set():
        # Still starting up (e.g. blocking external IP lookup): nothing to clean up yet
        raise SystemExit(0)


# Register before the project imports: importing influxdb_client alone takes
# several seconds, and as PID 1 an unhandled SIGTERM would just be ignored
# until Docker kills the container.
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

from config import load_config, LOGS_DIR  # noqa: E402
from log_watcher import LogWatcher  # noqa: E402
from log_parser import parse_log_line  # noqa: E402
from geo_lookup import GeoLookup  # noqa: E402
from abuse_checker import AbuseChecker  # noqa: E402
from ua_parser_util import parse_user_agent  # noqa: E402
from influx_writer import InfluxWriter  # noqa: E402
from ip_classifier import IPClassifier  # noqa: E402


def main():
    logger.info("npmGrafStats %s starting (log_level=%s, verbose=%s)", VERSION, _log_level, VERBOSE)

    cfg = load_config()

    geo = GeoLookup(cfg["has_city_db"], cfg["has_asn_db"])
    abuse = AbuseChecker(cfg["abuseip_key"], cfg["abuseip_cache_ttl_hours"])
    influx = InfluxWriter(cfg["influx_host"], cfg["influx_token"], cfg["influx_org"], cfg["influx_bucket"])
    classifier = IPClassifier(cfg["external_ip"], cfg["has_monitoring_file"])

    _stats = {"processed": 0, "errors": 0, "written": 0, "skipped": 0}
    _stats_lock = threading.Lock()

    def handle_line(line: str):
        entry = parse_log_line(line)
        if not entry:
            logger.debug("Failed to parse line: %.200s", line)
            return

        if _is_healthcheck(entry.user_agent):
            logger.debug("Skipped healthcheck from %s -> %s", entry.outside_ip, entry.domain)
            with _stats_lock:
                _stats["skipped"] += 1
            return

        ip_type = classifier.classify(entry.outside_ip)
        ua_info = parse_user_agent(entry.user_agent)

        if VERBOSE:
            logger.info("[REQ] %s -> %s (status=%d, len=%d, type=%s)",
                        entry.outside_ip, entry.domain,
                        entry.status_code, entry.length, ip_type)

        try:
            if ip_type == "internal":
                logger.debug("Internal IP: %s -> %s", entry.outside_ip, entry.domain)
                if cfg["internal_logs"]:
                    influx.write_internal(
                        "InternalRProxyIPs", entry.outside_ip, entry.domain,
                        entry.length, TARGET_PLACEHOLDER, entry.timestamp,
                        entry.status_code, ua_info,
                    )
            elif ip_type == "monitoring":
                logger.debug("Monitoring IP: %s -> %s", entry.outside_ip, entry.domain)
                if cfg["monitoring_logs"]:
                    geo_result = geo.lookup(entry.outside_ip)
                    abuse_scores = abuse.check(entry.outside_ip)
                    influx.write_external(
                        "MonitoringRProxyIPs", entry.outside_ip, entry.domain,
                        entry.length, TARGET_PLACEHOLDER, entry.timestamp,
                        entry.status_code, ua_info, geo_result, abuse_scores,
                        abuse_enabled=abuse.enabled,
                    )
            else:
                geo_result = geo.lookup(entry.outside_ip)
                abuse_scores = abuse.check(entry.outside_ip)
                influx.write_external(
                    "ReverseProxyConnections", entry.outside_ip, entry.domain,
                    entry.length, TARGET_PLACEHOLDER, entry.timestamp,
                    entry.status_code, ua_info, geo_result, abuse_scores,
                    abuse_enabled=abuse.enabled,
                )
            with _stats_lock:
                _stats["written"] += 1
        except Exception as e:
            logger.error("InfluxDB write FAILED for %s %s: %s", entry.outside_ip, entry.domain, e)
            with _stats_lock:
                _stats["errors"] += 1

        with _stats_lock:
            _stats["processed"] += 1

    threads: list[threading.Thread] = []
    watched: set[str] = set()
    log_patterns = ["access.log", "*_proxy.log"]

    def start_watchers(initial: bool) -> int:
        """Start a watcher for every matching log file not watched yet.
        Files found after startup are read from the beginning."""
        started = 0
        for pattern in log_patterns:
            for logfile in sorted(glob.glob(os.path.join(LOGS_DIR, pattern))):
                if logfile in watched:
                    continue
                watched.add(logfile)
                if not initial:
                    logger.info("New log file detected: %s", logfile)
                watcher = LogWatcher(logfile, handle_line, stop_event, from_start=not initial)
                t = threading.Thread(target=watcher.run, name=f"watch:{os.path.basename(logfile)}", daemon=True)
                t.start()
                threads.append(t)
                started += 1
        return started

    start_watchers(initial=True)
    if not threads:
        logger.warning("No log files found to watch yet in %s (patterns: %s), checking again every %ds",
                       LOGS_DIR, log_patterns, RESCAN_INTERVAL)
    else:
        logger.info("Started %d watcher threads", len(threads))


    _started.set()

    # Wait for stop, picking up log files of new hosts in the meantime
    try:
        while not stop_event.wait(RESCAN_INTERVAL):
            start_watchers(initial=False)
    except KeyboardInterrupt:
        stop_event.set()

    logger.info("Stats: processed=%d written=%d errors=%d skipped=%d",
                _stats["processed"], _stats["written"], _stats["errors"], _stats["skipped"])
    logger.info("Waiting for threads to finish...")
    for t in threads:
        t.join(timeout=5)

    abuse.close()
    influx.close()
    geo.close()
    logger.info("npmGrafStats shutdown complete")


if __name__ == "__main__":
    main()
