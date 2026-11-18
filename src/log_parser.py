"""Compiled regex parser for NPMplus access log format.

NPMplus uses a single combined access log (proxy + redirect requests are
not separated like in upstream NPM). Default log_format:

    [$time_local] $host $remote_addr $request_time "$request"
    $status $body_bytes_sent $bytes_sent $http_referer $http_user_agent

Example:
    [04/May/2026:17:22:29 +0200] test.wieser-server.de 217.237.83.97 0.009
    "GET / HTTP/1.1" 200 2928 3382 - Mozilla/5.0 (X11; Linux x86_64) ...

Field notes:
  - host can be an IP:port (admin UI, healthcheck) or a virtual hostname
  - referer and user_agent are NOT quoted; user_agent is the rest of the line
  - upstream/target IP is NOT logged
"""

import re
import logging

logger = logging.getLogger(__name__)

# --- IP patterns (non-capturing) ---

_IPV4 = r'(?:(?:\d{1,3}\.){3}\d{1,3})'
_IPV6 = (
    r'(?:'
    r'(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|'
    r'(?:[0-9a-fA-F]{1,4}:){1,7}:|'
    r'(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|'
    r'(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|'
    r'(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|'
    r'(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|'
    r'(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|'
    r'[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}|'
    r':(?::[0-9a-fA-F]{1,4}){1,7}|'
    r'::1'
    r')'
)
_IP = rf'(?:{_IPV4}|{_IPV6})'

# --- NPMplus access log regex ---
#
# Capture groups:
#   1: timestamp
#   2: host        (server name; may include :port)
#   3: client_ip   (remote_addr)
#   4: status_code
#   5: bytes_sent  (the third numeric column = total response size)
#   6: user_agent  (rest of the line)
_NPMPLUS_RE = re.compile(
    r'^\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+\-]\d{4})\]'  # [timestamp]
    r'\s+(\S+)'                                                # host
    r'\s+(' + _IP + r')'                                       # client IP
    r'\s+\S+'                                                  # request_time
    r'\s+"[^"]*"'                                              # "method path version"
    r'\s+(\d{3})'                                              # status
    r'\s+\d+'                                                  # body_bytes_sent
    r'\s+(\d+)'                                                # bytes_sent
    r'\s+\S+'                                                  # referer
    r'\s+(.+?)\s*$'                                            # user_agent (rest of line)
)


class LogEntry:
    __slots__ = ('timestamp', 'status_code', 'outside_ip', 'domain', 'length', 'user_agent')

    def __init__(self, timestamp, status_code, outside_ip, domain, length, user_agent):
        self.timestamp = timestamp
        self.status_code = status_code
        self.outside_ip = outside_ip
        self.domain = domain
        self.length = length
        self.user_agent = user_agent


def parse_log_line(line: str) -> LogEntry | None:
    """Parse a single NPMplus access log line."""
    m = _NPMPLUS_RE.match(line)
    if m:
        try:
            status_code = int(m.group(4))
            length = int(m.group(5))
        except ValueError:
            return None
        return LogEntry(
            timestamp=m.group(1),
            status_code=status_code,
            outside_ip=m.group(3),
            domain=m.group(2),
            length=length,
            user_agent=m.group(6),
        )
    return _fallback_parse(line)


def _fallback_parse(line: str) -> LogEntry | None:
    """Field-based fallback for lines the regex doesn't match.

    NPMplus space-split layout:
      0:[TS  1:+0000]  2:host  3:client_ip  4:req_time  5:"METHOD
      6:path  7:VERSION"  8:status  9:body_bytes  10:bytes_sent
      11:referer  12+:user_agent
    """
    if len(line) < 28 or line[0] != '[':
        return None

    timestamp = line[1:27]
    parts = line.split(' ', 12)
    if len(parts) < 12:
        return None

    try:
        status_code = int(parts[8])
        length = int(parts[10])
    except (ValueError, IndexError):
        return None

    return LogEntry(
        timestamp=timestamp,
        status_code=status_code,
        outside_ip=parts[3],
        domain=parts[2],
        length=length,
        user_agent=parts[12].rstrip('\r\n') if len(parts) > 12 else '',
    )
