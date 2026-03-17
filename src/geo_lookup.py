"""Persistent GeoIP City + ASN lookups."""

import logging
import geoip2.database
import geoip2.errors
from config import CITY_DB_PATH, ASN_DB_PATH

logger = logging.getLogger(__name__)


class GeoResult:
    __slots__ = ('latitude', 'longitude', 'iso_code', 'country', 'state', 'city', 'zip_code', 'asn')

    def __init__(self):
        self.latitude = 0.0
        self.longitude = 0.0
        self.iso_code = ""
        self.country = ""
        self.state = ""
        self.city = ""
        self.zip_code = ""
        self.asn = ""


class GeoLookup:
    def __init__(self, has_city_db: bool, has_asn_db: bool):
        self._city_reader = None
        self._asn_reader = None
        if has_city_db:
            try:
                self._city_reader = geoip2.database.Reader(CITY_DB_PATH)
                logger.info("GeoIP City DB opened")
            except Exception as e:
                logger.error("Failed to open City DB: %s", e)
        if has_asn_db:
            try:
                self._asn_reader = geoip2.database.Reader(ASN_DB_PATH)
                logger.info("GeoIP ASN DB opened")
            except Exception as e:
                logger.error("Failed to open ASN DB: %s", e)

    def lookup(self, ip: str) -> GeoResult:
        result = GeoResult()
        if self._city_reader:
            try:
                resp = self._city_reader.city(ip)
                result.latitude = resp.location.latitude or 0.0
                result.longitude = resp.location.longitude or 0.0
                result.iso_code = resp.country.iso_code or ""
                result.country = resp.country.name or ""
                result.state = resp.subdivisions.most_specific.name or "" if resp.subdivisions else ""
                result.city = resp.city.name or ""
                result.zip_code = resp.postal.code or ""
            except geoip2.errors.AddressNotFoundError:
                logger.debug("City DB: address not found for %s", ip)
            except Exception as e:
                logger.warning("City lookup error for %s: %s", ip, e)

        if self._asn_reader:
            try:
                resp = self._asn_reader.asn(ip)
                result.asn = resp.autonomous_system_organization or ""
            except geoip2.errors.AddressNotFoundError:
                result.asn = "No ASN associated"
            except Exception as e:
                result.asn = f"ASN error: {e}"

        return result

    def close(self):
        if self._city_reader:
            self._city_reader.close()
        if self._asn_reader:
            self._asn_reader.close()
