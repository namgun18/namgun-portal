"""Rule-based User-Agent parser with LRU cache."""

import re
from functools import lru_cache


_BROWSER_PATTERNS = [
    (re.compile(r"Edg(?:e|A)?/([\d.]+)"), "Edge"),
    (re.compile(r"OPR/([\d.]+)"), "Opera"),
    (re.compile(r"(?:CriOS|Chrome)/([\d.]+)"), "Chrome"),
    (re.compile(r"(?:FxiOS|Firefox)/([\d.]+)"), "Firefox"),
    (re.compile(r"Version/([\d.]+).*Safari"), "Safari"),
    (re.compile(r"Safari/([\d.]+)"), "Safari"),
]

_OS_PATTERNS = [
    (re.compile(r"Windows NT 10\.0"), "Windows 10+"),
    (re.compile(r"Windows NT 6\.3"), "Windows 8.1"),
    (re.compile(r"Windows NT 6\.1"), "Windows 7"),
    (re.compile(r"Windows"), "Windows"),
    (re.compile(r"Mac OS X ([\d_]+)"), "macOS"),
    (re.compile(r"Android ([\d.]+)"), "Android"),
    (re.compile(r"iPhone|iPad|iPod"), "iOS"),
    (re.compile(r"Linux"), "Linux"),
    (re.compile(r"CrOS"), "Chrome OS"),
]

_DEVICE_MOBILE = re.compile(r"Mobile|Android.*Mobile|iPhone|iPod", re.I)
_DEVICE_TABLET = re.compile(r"iPad|Android(?!.*Mobile)|Tablet", re.I)
_BOT = re.compile(r"bot|crawl|spider|slurp|wget|curl|python-requests", re.I)


@lru_cache(maxsize=1024)
def parse_user_agent(ua: str) -> tuple[str | None, str | None, str | None]:
    """Returns (browser, os, device). All nullable."""
    if not ua:
        return None, None, None

    if _BOT.search(ua):
        return "Bot", None, "Bot"

    # Browser
    browser = None
    for pattern, name in _BROWSER_PATTERNS:
        m = pattern.search(ua)
        if m:
            browser = name
            break

    # OS
    os_name = None
    for pattern, name in _OS_PATTERNS:
        if pattern.search(ua):
            os_name = name
            break

    # Device
    if _DEVICE_TABLET.search(ua):
        device = "Tablet"
    elif _DEVICE_MOBILE.search(ua):
        device = "Mobile"
    else:
        device = "Desktop"

    return browser, os_name, device
