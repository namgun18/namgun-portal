"""Auth API routes: login, me, logout, register, profile, password management."""

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.rate_limit import limiter
from app.auth.deps import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_DEFAULT,
    SESSION_MAX_AGE_REMEMBER,
    get_current_user,
    sign_value,
)
from app.auth.password import hash_password, verify_password
from app.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Helper: session cookie response ──────────────────────────


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


# ── POST /api/auth/login ─────────────────────────────────────


@router.post("/login")
@limiter.limit("10/minute")
async def login_post(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with username and password (bcrypt)."""
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="사용자명 또는 비밀번호가 올바르지 않습니다")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="계정이 비활성 상태입니다. 관리자 승인을 기다려주세요.")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    max_age = SESSION_MAX_AGE_REMEMBER if body.remember_me else SESSION_MAX_AGE_DEFAULT
    return _session_response(user, max_age=max_age)


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

    # Generate email verification token
    verify_token = secrets.token_urlsafe(32)

    # Create portal DB record with bcrypt password hash
    user = User(
        username=body.username,
        display_name=body.display_name,
        email=email,
        recovery_email=body.recovery_email,
        password_hash=hash_password(body.password),
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

    # Notify admins of new registration
    try:
        await _send_admin_registration_notify(body.username, body.display_name, email, body.recovery_email)
    except Exception:
        pass

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
    if body.display_name is not None:
        user.display_name = body.display_name

    if body.recovery_email is not None:
        user.recovery_email = body.recovery_email

    await db.commit()
    await db.refresh(user)
    return {"message": "프로필이 수정되었습니다"}


# ── POST /api/auth/change-password — 비밀번호 변경 ──────────


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password (requires current password verification)."""
    if not user.password_hash or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=400, detail="현재 비밀번호가 올바르지 않습니다"
        )

    user.password_hash = hash_password(body.new_password)
    await db.commit()

    return {"message": "비밀번호가 변경되었습니다"}


# ── POST /api/auth/forgot-password — 비밀번호 찾기 ──────────


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """Send password reset link to recovery email."""
    result = await db.execute(
        select(User).where(User.username == body.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    # Always return success to prevent username enumeration
    success_msg = "등록된 복구 이메일로 비밀번호 재설정 링크를 전송했습니다."

    if not user or not user.recovery_email:
        return {"message": success_msg}

    # Generate self-managed reset token
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_sent_at = datetime.now(timezone.utc)
    await db.commit()

    reset_url = f"{settings.app_url}/reset-password?token={token}"
    try:
        await _send_recovery_email(user.recovery_email, user.username, reset_url)
    except Exception:
        pass  # Silently fail to prevent info leakage

    return {"message": success_msg}


# ── POST /api/auth/reset-password — 비밀번호 재설정 ──────────


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using a token from forgot-password email."""
    result = await db.execute(
        select(User).where(User.password_reset_token == body.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="유효하지 않은 재설정 링크입니다")

    # Check expiry (1 hour)
    if user.password_reset_sent_at:
        elapsed = (datetime.now(timezone.utc) - user.password_reset_sent_at).total_seconds()
        if elapsed > 3600:
            raise HTTPException(status_code=400, detail="재설정 링크가 만료되었습니다")

    user.password_hash = hash_password(body.new_password)
    user.password_reset_token = None
    user.password_reset_sent_at = None
    await db.commit()

    return {"message": "비밀번호가 재설정되었습니다. 로그인해주세요."}


# ── Email helpers ────────────────────────────────────────────


def _smtp_send(msg) -> None:
    """Send email via SMTP (blocking, meant to be called via asyncio.to_thread)."""
    import smtplib

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


async def _send_verify_email(
    to_email: str, username: str, verify_url: str
) -> None:
    """Send email verification link via Stalwart SMTP."""
    import asyncio
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

    await asyncio.to_thread(_smtp_send, msg)


async def _send_recovery_email(
    to_email: str, username: str, recovery_link: str
) -> None:
    """Send recovery email via Stalwart SMTP."""
    import asyncio
    from email.mime.text import MIMEText

    msg = MIMEText(
        f"{username}님, 아래 링크를 클릭하여 비밀번호를 재설정하세요:\n\n"
        f"{recovery_link}\n\n"
        f"이 링크는 1시간 후 만료됩니다.\n"
        f"본인이 요청하지 않은 경우 이 메일을 무시하세요.",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "[namgun.or.kr] 비밀번호 재설정"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email

    await asyncio.to_thread(_smtp_send, msg)


async def _send_admin_registration_notify(
    username: str, display_name: str, email: str, recovery_email: str
) -> None:
    """Notify admins when a new user registers."""
    import asyncio
    from email.mime.text import MIMEText

    admin_list = [e.strip() for e in settings.admin_emails.split(",") if e.strip()]
    if not admin_list:
        return

    msg = MIMEText(
        f"새로운 가입 신청이 접수되었습니다.\n\n"
        f"  사용자명: {username}\n"
        f"  표시 이름: {display_name or '(없음)'}\n"
        f"  포털 메일: {email}\n"
        f"  복구 이메일: {recovery_email}\n\n"
        f"포털 관리 페이지에서 승인/거절해주세요:\n"
        f"{settings.app_url}/admin/users",
        "plain",
        "utf-8",
    )
    msg["Subject"] = f"[namgun.or.kr] 새 가입 신청: {username}"
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(admin_list)

    await asyncio.to_thread(_smtp_send, msg)
