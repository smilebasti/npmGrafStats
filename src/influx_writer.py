"""Persistent InfluxDB writer - single writes per log line."""

import logging
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)

_MONTH_MAP = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
}


def _convert_timestamp(raw: str) -> str:
    """Convert '01/Jan/2024:12:00:00 +0000' to ISO format."""
    # raw = "DD/Mon/YYYY:HH:MM:SS +ZZZZ"
    month = _MONTH_MAP.get(raw[3:6], '12')
    return f"{raw[7:11]}-{month}-{raw[0:2]}T{raw[12:20]}{raw[21:24]}:{raw[24:26]}"


class InfluxWriter:
    def __init__(self, host: str, token: str, org: str, bucket: str):
        self._org = org
        self._bucket = bucket
        self._client = influxdb_client.InfluxDBClient(url=host, token=token, org=org)
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        logger.info("InfluxDB client connected to %s", host)

    def write_external(self, measurement: str, ip: str, domain: str, length: int,
                       target_ip: str, timestamp: str, status_code: int,
                       user_agent_info: tuple, geo, abuse_scores: tuple,
                       abuse_enabled: bool = False):
        """Write an external/monitoring IP data point."""
        browser, browser_version, os_family = user_agent_info
        confidence_score, total_reports = abuse_scores
        time_str = _convert_timestamp(timestamp)

        point = influxdb_client.Point(measurement)
        # Tags (exactly matching original Getipinfo.py)
        point.tag("key", geo.iso_code)
        point.tag("latitude", geo.latitude)
        point.tag("longitude", geo.longitude)
        point.tag("Domain", domain)
        point.tag("City", geo.city)
        point.tag("State", geo.state)
        point.tag("Name", geo.country)
        point.tag("IP", ip)
        point.tag("Target", target_ip)
        if geo.asn:
            point.tag("Asn", geo.asn)
        if abuse_enabled:
            point.tag("abuseConfidenceScore", str(confidence_score))
            point.tag("totalReports", str(total_reports))

        # Fields (exactly matching original)
        point.field("Domain", domain)
        point.field("latitude", geo.latitude)
        point.field("longitude", geo.longitude)
        point.field("State", geo.state)
        point.field("City", geo.city)
        point.field("key", geo.iso_code)
        point.field("IP", ip)
        point.field("Target", target_ip)
        point.field("browser", browser)
        point.field("browser_version", browser_version)
        point.field("os", os_family)
        if geo.asn:
            point.field("Asn", geo.asn)
        point.field("Name", geo.country)
        point.field("length", length)
        point.field("statuscode", status_code)
        point.field("metric", 1)
        if abuse_enabled:
            point.field("abuseConfidenceScore", str(confidence_score))
            point.field("totalReports", str(total_reports))

        point.time(time_str)
        self._write_api.write(bucket=self._bucket, org=self._org, record=point)

    def write_internal(self, measurement: str, ip: str, domain: str, length: int,
                       target_ip: str, timestamp: str, status_code: int,
                       user_agent_info: tuple):
        """Write an internal IP data point (no geo, no abuse)."""
        browser, browser_version, os_family = user_agent_info
        time_str = _convert_timestamp(timestamp)

        point = influxdb_client.Point(measurement)
        # Tags (exactly matching original Internalipinfo.py)
        point.tag("Domain", domain)
        point.tag("IP", ip)
        point.tag("Target", target_ip)

        # Fields
        point.field("Domain", domain)
        point.field("IP", ip)
        point.field("Target", target_ip)
        point.field("browser", browser)
        point.field("browser_version", browser_version)
        point.field("os", os_family)
        point.field("length", length)
        point.field("statuscode", status_code)
        point.field("metric", 1)

        point.time(time_str)
        self._write_api.write(bucket=self._bucket, org=self._org, record=point)

    def close(self):
        self._client.close()
        logger.info("InfluxDB client closed")
