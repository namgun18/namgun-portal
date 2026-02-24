"""Access logging middleware — captures all /api/ requests with async batch insert."""

import asyncio
import logging
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.db.session import async_session
from app.db.models import AccessLog
from app.middleware.geoip import lookup_country
from app.middleware.ua_parser import parse_user_agent

logger = logging.getLogger(__name__)

# Paths to skip logging
_SKIP_PREFIXES = ("/api/health", "/api/docs", "/api/openapi")

# Path prefix → service name mapping
_SERVICE_MAP = [
    ("/api/mail", "mail"),
    ("/api/calendar", "calendar"),
    ("/api/contacts", "contacts"),
    ("/api/files", "files"),
    ("/api/meetings", "meetings"),
    ("/api/git", "git"),
    ("/api/lab", "lab"),
    ("/api/dashboard", "dashboard"),
    ("/api/admin", "admin"),
    ("/api/auth", "auth"),
    ("/api/services", "services"),
]

# Buffer for batch insertion
_buffer: deque[dict] = deque()
_BATCH_SIZE = 50
_FLUSH_INTERVAL = 5  # seconds
_flusher_running = False


def _classify_service(path: str) -> str | None:
    for prefix, name in _SERVICE_MAP:
        if path.startswith(prefix):
            return name
    return None


def _extract_user_id(request: Request) -> str | None:
    """Extract user_id from portal_session cookie without DB lookup."""
    from itsdangerous import URLSafeTimedSerializer, BadSignature
    from app.config import get_settings

    cookie = request.cookies.get("portal_session")
    if not cookie:
        return None
    try:
        settings = get_settings()
        s = URLSafeTimedSerializer(settings.secret_key)
        data = s.loads(cookie, max_age=86400 * 7)
        return data.get("user_id") if isinstance(data, dict) else None
    except (BadSignature, Exception):
        return None


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not path.startswith("/api/") or any(path.startswith(s) for s in _SKIP_PREFIXES):
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        # Extract IP (X-Real-IP from nginx, fallback to client)
        ip = request.headers.get("x-real-ip") or request.headers.get(
            "x-forwarded-for", ""
        ).split(",")[0].strip()
        if not ip and request.client:
            ip = request.client.host

        ua = request.headers.get("user-agent", "")
        browser, os_name, device = parse_user_agent(ua)
        country_code, country_name = lookup_country(ip) if ip else (None, None)
        user_id = _extract_user_id(request)
        service = _classify_service(path)

        _buffer.append({
            "id": str(uuid.uuid4()),
            "ip_address": ip or "unknown",
            "method": request.method,
            "path": path[:2048],
            "status_code": response.status_code,
            "response_time_ms": elapsed_ms,
            "user_agent": ua[:512] if ua else None,
            "browser": browser,
            "os": os_name,
            "device": device,
            "country_code": country_code,
            "country_name": country_name,
            "user_id": user_id,
            "service": service,
            "created_at": datetime.now(timezone.utc),
        })

        # Flush immediately if batch full
        if len(_buffer) >= _BATCH_SIZE:
            asyncio.create_task(_flush_buffer())

        return response


async def _flush_buffer() -> None:
    """Flush buffered log entries to DB."""
    if not _buffer:
        return
    entries = []
    while _buffer:
        try:
            entries.append(_buffer.popleft())
        except IndexError:
            break
    if not entries:
        return
    try:
        async with async_session() as session:
            session.add_all([AccessLog(**e) for e in entries])
            await session.commit()
    except Exception as e:
        logger.error("Failed to flush %d access logs: %s", len(entries), e)


async def run_log_flusher() -> None:
    """Background task: flush buffer every N seconds."""
    global _flusher_running
    _flusher_running = True
    while _flusher_running:
        await asyncio.sleep(_FLUSH_INTERVAL)
        await _flush_buffer()


async def run_log_cleanup() -> None:
    """Background task: delete logs older than 90 days, runs daily at 03:00 KST."""
    from sqlalchemy import delete, text
    while True:
        # Sleep until next 03:00 KST (UTC+9 = 18:00 UTC)
        now = datetime.now(timezone.utc)
        target_hour = 18  # 03:00 KST = 18:00 UTC
        next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if now.hour >= target_hour:
            next_run = next_run.replace(day=now.day + 1)
        delta = (next_run - now).total_seconds()
        if delta < 60:
            delta = 86400  # avoid tight loop
        await asyncio.sleep(delta)

        try:
            async with async_session() as session:
                result = await session.execute(
                    delete(AccessLog).where(
                        AccessLog.created_at < text("NOW() - INTERVAL '90 days'")
                    )
                )
                await session.commit()
                if result.rowcount:
                    logger.info("Cleaned up %d old access logs", result.rowcount)
        except Exception as e:
            logger.error("Log cleanup failed: %s", e)
