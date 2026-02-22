import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.db.session import init_db
from app.auth.router import router as auth_router
from app.auth.oauth_provider import router as oauth_router
from app.services.router import router as services_router
from app.services.health import run_health_checker
from app.files.router import router as files_router
from app.mail.router import router as mail_router
from app.meetings.router import router as meetings_router
from app.admin.router import router as admin_router
from app.git.router import router as git_router
from app.dashboard.router import router as dashboard_router
from app.lab.router import router as lab_router
from app.calendar.router import router as calendar_router
from app.contacts.router import router as contacts_router

settings = get_settings()
_health_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _health_task

    await init_db()
    _health_task = asyncio.create_task(run_health_checker())
    print(f"[STARTUP] {settings.app_name} 시작됨")

    yield

    if _health_task:
        _health_task.cancel()
        try:
            await _health_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=settings.app_name,
    version="0.7.1",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url=None,
)

app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(services_router)
app.include_router(files_router)
app.include_router(mail_router)
app.include_router(meetings_router)
app.include_router(admin_router)
app.include_router(git_router)
app.include_router(dashboard_router)
app.include_router(lab_router)
app.include_router(calendar_router)
app.include_router(contacts_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name, "version": "0.7.1"}


@app.get("/m/{code}")
async def short_url_redirect(code: str):
    """Redirect short meeting invite code to guest join page."""
    from app.meetings.router import _short_codes
    meeting_id = _short_codes.get(code)
    if not meeting_id:
        return RedirectResponse("/")
    return RedirectResponse(f"/join/{meeting_id}")
