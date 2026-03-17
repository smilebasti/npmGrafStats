"""Compiled regex parsers for NPM proxy-host and redirection log formats.

NPM generates two types of access logs with DIFFERENT formats:

  Proxy-host (has [Sent-to]):
    [DD/Mon/YYYY:HH:MM:SS +0000] - STATUS STATUS - METHOD SCHEME DOMAIN "PATH"
      [Client IP] [Length N] [Gzip -] [Sent-to IP] "UA" "REFERER"

  Redirection (NO [Sent-to], only one status code):
    [DD/Mon/YYYY:HH:MM:SS +0000] STATUS - METHOD SCHEME DOMAIN "PATH"
      [Client IP] [Length N] [Gzip -] "UA" "REFERER"

Key differences:
  - Proxy has "- STATUS STATUS -" after timestamp, redirect has "STATUS -"
  - Proxy has [Sent-to IP] before the UA, redirect does not
  - Field indices shift by 2 between formats (proxy domain=index 8, redirect domain=index 6)
"""

import re
import logging

logger = logging.getLogger(__name__)

# --- IP patterns (non-capturing, used inside capturing groups in the regexes) ---

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
# Combined pattern matching both IPv4 and IPv6
_IP = rf'(?:{_IPV4}|{_IPV6})'

# --- Proxy-host log regex ---
# Example: [12/Mar/2026:00:44:15 +0000] - 500 500 - POST http hausi.example.com "/" [Client 1.2.3.4] [Length 63] [Gzip -] [Sent-to 10.0.0.1] "Mozilla/5.0 ..." "-"
#
# Capture groups:
#   1: timestamp    (DD/Mon/YYYY:HH:MM:SS +0000)
#   2: status_code  (first of the two status codes)
#   3: domain       (unquoted hostname)
#   4: client_ip    (from [Client ...])
#   5: length       (from [Length ...])
#   6: target_ip    (from [Sent-to ...])
#   7: user_agent   (first quoted string after [Sent-to])
_PROXY_RE = re.compile(
    r'^\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+\-]\d{4})\]'  # [timestamp]
    r'\s+-\s+'                         # " - " separator
    r'(\d{3})'                         # status code (first)
    r'\s+\d{3}\s+-\s+\w+\s+\w+\s+'    # second status, " - ", METHOD, SCHEME
    r'(\S+)'                           # domain (unquoted)
    r'\s+"[^"]*"'                      # "path"
    r'\s+\[Client\s+(' + _IP + r')\]'  # [Client IP]
    r'\s+\[Length\s+(\d+)\]'           # [Length N]
    r'\s+\[Gzip\s+[^\]]*\]'           # [Gzip ...]
    r'\s+\[Sent-to\s+(' + _IP + r')\]'  # [Sent-to IP]
    r'\s+"([^"]*)"'                    # "user-agent"
)

# --- Redirection log regex ---
# Example: [08/Mar/2026:15:10:15 +0000] 301 - GET http www.cycling-basti.de "/" [Client 43.130.67.6] [Length 166] [Gzip -] "Mozilla/5.0 ..." "-"
#
# Capture groups:
#   1: timestamp
#   2: status_code  (only one, unlike proxy)
#   3: domain
#   4: client_ip
#   5: user_agent
#
# Key difference to proxy: no [Sent-to], so after [Gzip] comes "UA" directly.
_REDIRECT_RE = re.compile(
    r'^\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+\-]\d{4})\]'  # [timestamp]
    r'\s+'
    r'(\d{3})'                         # status code
    r'\s+-\s+\w+\s+\w+\s+'            # " - ", METHOD, SCHEME
    r'(\S+)'                           # domain (unquoted)
    r'\s+"[^"]*"'                      # "path"
    r'\s+\[Client\s+(' + _IP + r')\]'  # [Client IP]
    r'\s+\[Length\s+\d+\]'             # [Length N] (value not captured)
    r'\s+\[Gzip\s+[^\]]*\]'           # [Gzip ...]
    r'\s+"([^"]*)"'                    # "user-agent" (directly after Gzip, no Sent-to)
)


# --- Data classes ---

class ProxyLogEntry:
    __slots__ = ('timestamp', 'status_code', 'outside_ip', 'domain', 'length', 'target_ip', 'user_agent')

    def __init__(self, timestamp, status_code, outside_ip, domain, length, target_ip, user_agent):
        self.timestamp = timestamp
        self.status_code = status_code
        self.outside_ip = outside_ip
        self.domain = domain
        self.length = length
        self.target_ip = target_ip
        self.user_agent = user_agent


class RedirectLogEntry:
    __slots__ = ('timestamp', 'status_code', 'outside_ip', 'domain', 'user_agent')

    def __init__(self, timestamp, status_code, outside_ip, domain, user_agent):
        self.timestamp = timestamp
        self.status_code = status_code
        self.outside_ip = outside_ip
        self.domain = domain
        self.user_agent = user_agent


# --- Parsers ---

def parse_proxy_line(line: str) -> ProxyLogEntry | None:
    """Parse a proxy-host access log line. Falls back to field-based extraction."""
    m = _PROXY_RE.match(line)
    if m:
        return ProxyLogEntry(
            timestamp=m.group(1),
            status_code=int(m.group(2)),
            outside_ip=m.group(4),
            domain=m.group(3),
            length=int(m.group(5)),
            target_ip=m.group(6),
            user_agent=m.group(7),
        )
    return _fallback_proxy_parse(line)


def parse_redirect_line(line: str) -> RedirectLogEntry | None:
    """Parse a redirection-host access log line. Falls back to field-based extraction."""
    m = _REDIRECT_RE.match(line)
    if m:
        return RedirectLogEntry(
            timestamp=m.group(1),
            status_code=int(m.group(2)),
            outside_ip=m.group(4),
            domain=m.group(3),
            user_agent=m.group(5),
        )
    return _fallback_redirect_parse(line)


# --- Fallback parsers (for edge cases the regex doesn't cover) ---

def _fallback_proxy_parse(line: str) -> ProxyLogEntry | None:
    """Field-based proxy parser. Extracts known fields by pattern/position."""
    if len(line) < 28 or line[0] != '[':
        return None

    timestamp = line[1:27]

    client_match = re.search(r'\[Client\s+(' + _IP + r')\]', line)
    if not client_match:
        return None
    outside_ip = client_match.group(1)

    sentto_match = re.search(r'\[Sent-to\s+(' + _IP + r')\]', line)
    target_ip = sentto_match.group(1) if sentto_match else outside_ip

    parts = line.split()

    # Proxy format field indices (space-split):
    # 0:[TS 1:+0000] 2:- 3:STATUS 4:STATUS 5:- 6:METHOD 7:SCHEME 8:DOMAIN ...
    domain = parts[8] if len(parts) > 8 else "unknown"

    try:
        status_code = int(parts[3]) if len(parts) > 3 else 0
    except ValueError:
        status_code = 0

    # Find [Length N] anywhere in the line
    length = 0
    for i, p in enumerate(parts):
        if p == '[Length' and i + 1 < len(parts):
            try:
                length = int(parts[i + 1].rstrip(']'))
            except ValueError:
                pass
            break

    # UA is the first quoted string after [Sent-to] or [Gzip]
    ua_match = re.search(r'\[Sent-to [^\]]+\]\s*"([^"]*)"', line)
    if not ua_match:
        ua_match = re.search(r'\[Gzip\s+[^\]]*\]\s*"([^"]*)"', line)
    user_agent = ua_match.group(1) if ua_match else ""

    return ProxyLogEntry(timestamp, status_code, outside_ip, domain, length, target_ip, user_agent)


def _fallback_redirect_parse(line: str) -> RedirectLogEntry | None:
    """Field-based redirect parser. No [Sent-to] field in redirects."""
    if len(line) < 28 or line[0] != '[':
        return None

    timestamp = line[1:27]

    client_match = re.search(r'\[Client\s+(' + _IP + r')\]', line)
    if not client_match:
        return None
    outside_ip = client_match.group(1)

    parts = line.split()

    # Redirect format field indices (space-split):
    # 0:[TS 1:+0000] 2:STATUS 3:- 4:METHOD 5:SCHEME 6:DOMAIN ...
    domain = parts[6] if len(parts) > 6 else "unknown"

    try:
        status_code = int(parts[2]) if len(parts) > 2 else 0
    except ValueError:
        status_code = 0

    # UA is the first quoted string after [Gzip] (no [Sent-to] in redirects)
    ua_match = re.search(r'\[Gzip\s+[^\]]*\]\s*"([^"]*)"', line)
    user_agent = ua_match.group(1) if ua_match else ""

    return RedirectLogEntry(timestamp, status_code, outside_ip, domain, user_agent)
