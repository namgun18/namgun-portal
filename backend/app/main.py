import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.rate_limit import limiter
from app.db.session import init_db
from app.middleware.access_log import AccessLogMiddleware, run_log_flusher, run_log_cleanup
from app.middleware.geoip import init_geoip
from app.auth.router import router as auth_router
from app.auth.oauth_provider import router as oauth_router
from app.services.router import router as services_router
from app.services.health import run_health_checker
from app.files.router import router as files_router
from app.mail.router import router as mail_router
from app.admin.router import router as admin_router
from app.git.router import router as git_router
from app.dashboard.router import router as dashboard_router
from app.lab.router import router as lab_router
from app.calendar.router import router as calendar_router
from app.contacts.router import router as contacts_router

settings = get_settings()
_health_task = None
_log_flusher_task = None
_log_cleanup_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _health_task, _log_flusher_task, _log_cleanup_task

    await init_db()
    init_geoip(settings.geoip_db_path)
    _health_task = asyncio.create_task(run_health_checker())
    _log_flusher_task = asyncio.create_task(run_log_flusher())
    _log_cleanup_task = asyncio.create_task(run_log_cleanup())
    print(f"[STARTUP] {settings.app_name} 시작됨")

    yield

    for task in (_health_task, _log_flusher_task, _log_cleanup_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title=settings.app_name,
    version="0.7.1",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url=None,
)

app.add_middleware(AccessLogMiddleware)

# Rate limit 초과 시 429 반환
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."},
    )

app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(services_router)
app.include_router(files_router)
app.include_router(mail_router)
app.include_router(admin_router)
app.include_router(git_router)
app.include_router(dashboard_router)
app.include_router(lab_router)
app.include_router(calendar_router)
app.include_router(contacts_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name, "version": "0.7.1"}


