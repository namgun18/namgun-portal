"""Auth API routes: server-side login, OIDC fallback, me, logout."""

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.auth.deps import (
    PKCE_COOKIE,
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    get_current_user,
    sign_value,
    unsign_value,
)
from app.auth.oidc import (
    AuthenticationError,
    build_authorize_url,
    exchange_code,
    generate_pkce,
    get_userinfo,
    server_side_authenticate,
)
from app.auth.schemas import LoginRequest, UserResponse

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Helper: upsert user from Authentik userinfo ──────────────


async def _upsert_user(userinfo: dict, db: AsyncSession) -> User:
    sub = userinfo["sub"]
    groups = userinfo.get("groups", [])
    is_admin = settings.oidc_admin_group in groups

    result = await db.execute(select(User).where(User.authentik_sub == sub))
    user = result.scalar_one_or_none()

    if user:
        user.username = userinfo.get("preferred_username", user.username)
        user.display_name = userinfo.get("name")
        user.email = userinfo.get("email")
        user.avatar_url = userinfo.get("avatar")
        user.is_admin = is_admin
        user.last_login_at = datetime.now(timezone.utc)
    else:
        user = User(
            authentik_sub=sub,
            username=userinfo.get("preferred_username", sub),
            display_name=userinfo.get("name"),
            email=userinfo.get("email"),
            avatar_url=userinfo.get("avatar"),
            is_admin=is_admin,
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return user


def _session_response(user: User, body: dict | None = None) -> JSONResponse:
    session_data = sign_value({"user_id": user.id})
    response = JSONResponse(content=body or {"status": "ok"})
    response.set_cookie(
        SESSION_COOKIE,
        session_data,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        path="/",
    )
    return response


# ── POST /api/auth/login — server-side (primary) ────────────


@router.post("/login")
async def login_post(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate via Authentik Flow Executor (server-side)."""
    try:
        userinfo = await server_side_authenticate(body.username, body.password)
    except AuthenticationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    user = await _upsert_user(userinfo, db)
    return _session_response(user)


# ── GET /api/auth/login — redirect to Authentik (fallback) ───


@router.get("/login")
async def login_redirect():
    """Redirect to Authentik with PKCE (fallback for direct access)."""
    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = generate_pkce()

    authorize_url = build_authorize_url(state, code_challenge)

    pkce_data = sign_value({"state": state, "code_verifier": code_verifier})

    response = RedirectResponse(url=authorize_url, status_code=302)
    response.set_cookie(
        PKCE_COOKIE,
        pkce_data,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=600,
        path="/api/auth",
    )
    return response


# ── GET /api/auth/callback — Authentik redirect (fallback) ───


@router.get("/callback")
async def callback(
    code: str,
    state: str,
    portal_pkce: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Exchange code for tokens, create/update user, set session cookie."""
    if not portal_pkce:
        raise HTTPException(status_code=400, detail="Missing PKCE cookie")

    pkce_data = unsign_value(portal_pkce, max_age=600)
    if not pkce_data or pkce_data.get("state") != state:
        raise HTTPException(status_code=400, detail="Invalid state")

    tokens = await exchange_code(code, pkce_data["code_verifier"])
    userinfo = await get_userinfo(tokens["access_token"])
    user = await _upsert_user(userinfo, db)

    session_data = sign_value({"user_id": user.id})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        SESSION_COOKIE,
        session_data,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        path="/",
    )
    response.delete_cookie(PKCE_COOKIE, path="/api/auth")
    return response


# ── GET /api/auth/me ─────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    """Return current authenticated user info."""
    return user


# ── POST /api/auth/logout ───────────────────────────────────


@router.post("/logout")
async def logout():
    """Clear portal session cookie."""
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
