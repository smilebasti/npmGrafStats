"""User-Agent parsing utility."""

from ua_parser import user_agent_parser


def parse_user_agent(ua_string: str) -> tuple[str, str, str]:
    """Returns (browser, browser_version, os_family)."""
    parsed = user_agent_parser.Parse(ua_string)

    browser = parsed['user_agent']['family'] or 'Unknown'
    major = parsed['user_agent']['major'] or '0'
    browser_version = f"{browser}: {major}"
    if parsed['user_agent']['minor']:
        browser_version += f".{parsed['user_agent']['minor']}"

    os_family = parsed['os']['family'] or 'Unknown'

    return browser, browser_version, os_family
