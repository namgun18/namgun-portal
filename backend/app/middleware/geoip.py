"""GeoIP country lookup using MaxMind GeoLite2-Country DB."""

import ipaddress
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_reader = None
_available = False


def init_geoip(db_path: str) -> None:
    """Initialize the GeoIP reader. Call once at startup."""
    global _reader, _available
    if not Path(db_path).exists():
        logger.warning("GeoIP DB not found at %s — country lookup disabled", db_path)
        return
    try:
        import geoip2.database
        _reader = geoip2.database.Reader(db_path)
        _available = True
        logger.info("GeoIP initialized: %s", db_path)
    except Exception as e:
        logger.warning("GeoIP init failed: %s", e)


@lru_cache(maxsize=4096)
def lookup_country(ip: str) -> tuple[str | None, str | None]:
    """Returns (country_code, country_name). Both nullable."""
    if not _available or not _reader:
        return None, None
    try:
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_reserved:
            return None, None
        response = _reader.country(ip)
        code = response.country.iso_code
        name = response.country.names.get("ko") or response.country.name
        return code, name
    except Exception:
        return None, None
