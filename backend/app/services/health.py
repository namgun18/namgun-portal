"""Background service health checker with in-memory cache."""

import asyncio
import time

import httpx

from app.services.schemas import ServiceStatus

# Service definitions (MVP hardcoded)
SERVICE_DEFS = [
    {
        "name": "Authentik",
        "health_url": "http://192.168.0.50:9000/-/health/ready/",
        "external_url": "https://auth.namgun.or.kr",
        "internal_only": False,
    },
    {
        "name": "Gitea",
        "health_url": "http://192.168.0.50:3000/api/v1/version",
        "external_url": "https://git.namgun.or.kr/user/oauth2/authentik",
        "internal_only": False,
    },
    {
        "name": "RustDesk",
        "health_tcp": "192.168.0.50:21114",
        "external_url": "https://remote.namgun.or.kr",
        "internal_only": False,
    },
    {
        "name": "Game Panel",
        "health_url": "http://192.168.0.50:8090/api/health",
        "external_url": "https://game.namgun.or.kr",
        "internal_only": False,
    },
    {
        "name": "Stalwart Mail",
        "health_url": "http://192.168.0.250:8080/healthz",
        "external_url": "https://mail.namgun.or.kr",
        "internal_only": True,
    },
    {
        "name": "화상회의 (BBB)",
        "health_url": "https://meet.namgun.or.kr/bigbluebutton/api",
        "external_url": None,
        "internal_only": True,
    },
]

# In-memory cache
_cache: list[ServiceStatus] = []
_check_interval = 60  # seconds


async def check_service(svc: dict) -> ServiceStatus:
    """Check a single service health endpoint (HTTP or TCP)."""
    elapsed_ms = None
    status = "down"

    try:
        start = time.monotonic()
        if "health_tcp" in svc:
            host, port = svc["health_tcp"].rsplit(":", 1)
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, int(port)), timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            elapsed_ms = int((time.monotonic() - start) * 1000)
            status = "ok"
        else:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                resp = await client.get(svc["health_url"])
                elapsed_ms = int((time.monotonic() - start) * 1000)
                status = "ok" if resp.status_code < 400 else "down"
    except Exception:
        elapsed_ms = None
        status = "down"

    return ServiceStatus(
        name=svc["name"],
        url=svc["external_url"],
        status=status,
        response_ms=elapsed_ms,
        internal_only=svc["internal_only"],
    )


async def run_health_checker():
    """Background task: check all services every 60s."""
    global _cache
    while True:
        results = await asyncio.gather(
            *(check_service(svc) for svc in SERVICE_DEFS),
            return_exceptions=True,
        )
        _cache = [
            r if isinstance(r, ServiceStatus)
            else ServiceStatus(
                name="unknown", url=None, status="down",
                response_ms=None, internal_only=False,
            )
            for r in results
        ]
        await asyncio.sleep(_check_interval)


def get_cached_status() -> list[ServiceStatus]:
    """Return cached service statuses."""
    if not _cache:
        return [
            ServiceStatus(
                name=svc["name"],
                url=svc["external_url"],
                status="checking",
                response_ms=None,
                internal_only=svc["internal_only"],
            )
            for svc in SERVICE_DEFS
        ]
    return _cache
