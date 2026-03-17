"""Centralized configuration loaded from environment variables and files."""

import os
import logging

logger = logging.getLogger(__name__)

DATA_DIR = "/data"
GEOLITE_DIR = "/geolite"
LOGS_DIR = "/logs"

CITY_DB_PATH = os.path.join(GEOLITE_DIR, "GeoLite2-City.mmdb")
ASN_DB_PATH = os.path.join(GEOLITE_DIR, "GeoLite2-ASN.mmdb")
MONITORING_IPS_FILE = os.path.join(DATA_DIR, "monitoringips.txt")
INFLUX_TOKEN_FILE = os.path.join(DATA_DIR, "influxdb-token.txt")
ABUSEIP_KEY_FILE = os.path.join(DATA_DIR, "abuseipdb-key.txt")
ABUSEIP_CACHE_DB = os.path.join(DATA_DIR, "abuseip_cache.db")
ABUSEIP_CACHE_JSON = os.path.join(DATA_DIR, "abuseip_cache.json")
CACHE_TTL_HOURS = 48


def _read_file_stripped(path: str) -> str | None:
    try:
        with open(path, "r") as f:
            value = f.read().strip()
            return value if value else None
    except (OSError, IOError):
        return None


def load_config() -> dict:
    """Load and validate all configuration. Returns a config dict."""
    cfg = {}

    # InfluxDB
    cfg["influx_host"] = os.getenv("INFLUX_HOST", "http://influxdb:8086")
    cfg["influx_bucket"] = os.getenv("INFLUX_BUCKET", "npmgrafstats")
    cfg["influx_org"] = os.getenv("INFLUX_ORG", "npmgrafstats")

    cfg["influx_token"] = os.getenv("INFLUX_TOKEN") or _read_file_stripped(INFLUX_TOKEN_FILE)
    if not cfg["influx_token"]:
        raise SystemExit("No InfluxDB Token found. Set INFLUX_TOKEN or provide /data/influxdb-token.txt")

    # Feature flags
    cfg["redirection_logs"] = os.getenv("REDIRECTION_LOGS", "FALSE").upper()
    cfg["internal_logs"] = os.getenv("INTERNAL_LOGS", "FALSE").upper() == "TRUE"
    cfg["monitoring_logs"] = os.getenv("MONITORING_LOGS", "FALSE").upper() == "TRUE"

    # AbuseIPDB
    cfg["abuseip_key"] = os.getenv("ABUSEIP_KEY") or _read_file_stripped(ABUSEIP_KEY_FILE)

    # GeoIP availability
    cfg["has_city_db"] = os.path.isfile(CITY_DB_PATH)
    cfg["has_asn_db"] = os.path.isfile(ASN_DB_PATH)

    # Monitoring IPs file
    cfg["has_monitoring_file"] = os.path.isfile(MONITORING_IPS_FILE)

    # External IP (best-effort)
    cfg["external_ip"] = _get_external_ip()

    logger.info("Configuration loaded. redirection_logs=%s internal_logs=%s monitoring_logs=%s abuseip=%s asn_db=%s",
                cfg["redirection_logs"], cfg["internal_logs"], cfg["monitoring_logs"],
                bool(cfg["abuseip_key"]), cfg["has_asn_db"])
    return cfg


def _get_external_ip() -> str | None:
    try:
        import urllib.request
        with urllib.request.urlopen("https://ifconfig.me/ip", timeout=10) as resp:
            return resp.read().decode().strip()
    except Exception as e:
        logger.warning("Could not determine external IP: %s", e)
        return None
