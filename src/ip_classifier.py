"""Classify IPs as internal, external-own, monitoring, or external."""

import ipaddress
import logging
import os
from config import MONITORING_IPS_FILE

logger = logging.getLogger(__name__)


def _parse_networks(filepath: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Load CIDR networks and single IPs from monitoringips.txt."""
    networks = []
    if not os.path.isfile(filepath):
        return networks
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                networks.append(ipaddress.ip_network(line, strict=False))
            except ValueError:
                logger.warning("Invalid network in monitoring IPs file: %s", line)
    logger.info("Loaded %d monitoring networks/IPs", len(networks))
    return networks


class IPClassifier:
    def __init__(self, external_ip: str | None, has_monitoring_file: bool):
        self._external_ip = external_ip
        self._monitoring_nets = _parse_networks(MONITORING_IPS_FILE) if has_monitoring_file else []

    def classify(self, ip_str: str) -> str:
        """Returns 'internal', 'monitoring', or 'external'."""
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            return "external"

        # Loopback (127.0.0.0/8, ::1) and RFC1918/ULA/link-local are all internal
        if addr.is_loopback or addr.is_private or addr.is_link_local:
            return "internal"
        if self._external_ip and ip_str == self._external_ip:
            return "internal"

        # Check monitoring
        if self._monitoring_nets:
            if any(addr in net for net in self._monitoring_nets):
                return "monitoring"

        return "external"
