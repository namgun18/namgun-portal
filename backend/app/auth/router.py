"""Auth API routes: server-side login, OIDC fallback, me, logout, register, profile."""

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.rate_limit import limiter
from app.auth.deps import (
    PKCE_COOKIE,
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    SESSION_MAX_AGE_DEFAULT,
    SESSION_MAX_AGE_REMEMBER,
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
from app.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    UserResponse,
)
from app.auth.authentik_admin import (
    AuthentikAdminError,
    create_user as authentik_create_user,
    get_recovery_link,
    lookup_pk_by_username,
    set_password as authentik_set_password,
    update_user as authentik_update_user,
)

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


def _session_response(
    user: User,
    body: dict | None = None,
    max_age: int = SESSION_MAX_AGE_DEFAULT,
) -> JSONResponse:
    session_data = sign_value({"user_id": user.id})
    response = JSONResponse(content=body or {"status": "ok"})
    response.set_cookie(
        SESSION_COOKIE,
        session_data,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=max_age,
        path="/",
    )
    return response


# ── Helper: get Authentik PK (resolve + cache if missing) ────


async def _get_authentik_pk(user: User, db: AsyncSession | None = None) -> int:
    """Get Authentik numeric PK from user, resolving by username if not cached."""
    if user.authentik_pk:
        return user.authentik_pk
    # Resolve by username and cache
    pk = await lookup_pk_by_username(user.username)
    if not pk:
        raise HTTPException(status_code=404, detail="Authentik 사용자를 찾을 수 없습니다")
    if db:
        user.authentik_pk = pk
        await db.commit()
    return pk


# ── POST /api/auth/login — server-side (primary) ────────────


@router.post("/login")
@limiter.limit("10/minute")
async def login_post(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate via Authentik Flow Executor (server-side)."""
    try:
        userinfo = await server_side_authenticate(body.username, body.password)
    except AuthenticationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    user = await _upsert_user(userinfo, db)
    max_age = SESSION_MAX_AGE_REMEMBER if body.remember_me else SESSION_MAX_AGE_DEFAULT
    return _session_response(user, max_age=max_age)


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


# ── POST /api/auth/register — 회원가입 ──────────────────────


@router.post("/register", status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user (pending admin approval)."""
    email = f"{body.username}@namgun.or.kr"

    # Check if username already exists in portal DB
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="이미 사용 중인 사용자명입니다")

    # Create user in Authentik (is_active=False)
    try:
        authentik_user = await authentik_create_user(
            username=body.username,
            email=email,
            name=body.display_name,
            password=body.password,
            recovery_email=body.recovery_email,
        )
    except AuthentikAdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Generate email verification token
    verify_token = secrets.token_urlsafe(32)

    # Create portal DB record (uid = OIDC sub, pk = Admin API ID)
    user = User(
        authentik_sub=authentik_user["uid"],
        authentik_pk=authentik_user["pk"],
        username=body.username,
        display_name=body.display_name,
        email=email,
        recovery_email=body.recovery_email,
        email_verified=False,
        email_verify_token=verify_token,
        email_verify_sent_at=datetime.now(timezone.utc),
        is_active=False,
    )
    db.add(user)
    await db.commit()

    # Send verification email to recovery_email
    try:
        verify_url = f"{settings.app_url}/verify-email?token={verify_token}"
        await _send_verify_email(body.recovery_email, body.username, verify_url)
    except Exception:
        pass  # Don't fail registration if email fails

    return {"message": "가입 신청이 완료되었습니다. 복구 이메일로 전송된 인증 링크를 확인해주세요."}


# ── GET /api/auth/verify-email — 이메일 인증 ────────────────


@router.get("/verify-email")
async def verify_email(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Verify recovery email via token link."""
    result = await db.execute(
        select(User).where(User.email_verify_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="유효하지 않은 인증 링크입니다.")

    # Check token expiry (24 hours)
    if user.email_verify_sent_at:
        elapsed = (datetime.now(timezone.utc) - user.email_verify_sent_at).total_seconds()
        if elapsed > 86400:
            raise HTTPException(status_code=400, detail="인증 링크가 만료되었습니다. 다시 가입해주세요.")

    user.email_verified = True
    user.email_verify_token = None
    await db.commit()

    return {"message": "이메일 인증이 완료되었습니다. 관리자 승인 후 로그인이 가능합니다."}


# ── PATCH /api/auth/profile — 프로필 수정 ────────────────────


@router.patch("/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update display name and/or recovery email."""
    authentik_fields: dict = {}

    if body.display_name is not None:
        user.display_name = body.display_name
        authentik_fields["name"] = body.display_name

    if body.recovery_email is not None:
        user.recovery_email = body.recovery_email
        # Update Authentik attributes
        authentik_fields["attributes"] = {"recovery_email": body.recovery_email}

    if authentik_fields:
        try:
            pk = await _get_authentik_pk(user, db)
            await authentik_update_user(pk, **authentik_fields)
        except AuthentikAdminError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

    await db.commit()
    await db.refresh(user)
    return {"message": "프로필이 수정되었습니다"}


# ── POST /api/auth/change-password — 비밀번호 변경 ──────────


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
):
    """Change password (requires current password verification)."""
    # Verify current password via Authentik Flow Executor
    try:
        await server_side_authenticate(user.username, body.current_password)
    except AuthenticationError:
        raise HTTPException(
            status_code=400, detail="현재 비밀번호가 올바르지 않습니다"
        )

    # Set new password
    try:
        pk = await _get_authentik_pk(user)
        await authentik_set_password(pk, body.new_password)
    except AuthentikAdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return {"message": "비밀번호가 변경되었습니다"}


# ── POST /api/auth/forgot-password — 비밀번호 찾기 ──────────


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """Send password recovery link to recovery email."""
    result = await db.execute(
        select(User).where(User.username == body.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    # Always return success to prevent username enumeration
    success_msg = "등록된 복구 이메일로 비밀번호 재설정 링크를 전송했습니다."

    if not user or not user.recovery_email:
        return {"message": success_msg}

    try:
        pk = await _get_authentik_pk(user)
        recovery_link = await get_recovery_link(pk)
    except AuthentikAdminError:
        return {"message": success_msg}

    # Send recovery link via Stalwart SMTP
    try:
        await _send_recovery_email(user.recovery_email, user.username, recovery_link)
    except Exception:
        pass  # Silently fail to prevent info leakage

    return {"message": success_msg}


async def _send_verify_email(
    to_email: str, username: str, verify_url: str
) -> None:
    """Send email verification link via Stalwart SMTP."""
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(
        f"{username}님, 아래 링크를 클릭하여 이메일을 인증해주세요:\n\n"
        f"{verify_url}\n\n"
        f"이 링크는 24시간 후 만료됩니다.\n"
        f"본인이 요청하지 않은 경우 이 메일을 무시하세요.",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "[namgun.or.kr] 이메일 인증"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


async def _send_recovery_email(
    to_email: str, username: str, recovery_link: str
) -> None:
    """Send recovery email via Stalwart SMTP."""
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(
        f"{username}님, 아래 링크를 클릭하여 비밀번호를 재설정하세요:\n\n"
        f"{recovery_link}\n\n"
        f"이 링크는 일정 시간 후 만료됩니다.\n"
        f"본인이 요청하지 않은 경우 이 메일을 무시하세요.",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "[namgun.or.kr] 비밀번호 재설정"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
