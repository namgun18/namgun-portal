"""Authentication dependencies."""

from fastapi import Cookie, Depends, HTTPException, status
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db

settings = get_settings()
signer = URLSafeTimedSerializer(settings.secret_key)

SESSION_COOKIE = "portal_session"
PKCE_COOKIE = "portal_pkce"
SESSION_MAX_AGE = 86400 * 7  # 7 days


def sign_value(data: dict) -> str:
    return signer.dumps(data)


def unsign_value(token: str, max_age: int = SESSION_MAX_AGE) -> dict | None:
    try:
        return signer.loads(token, max_age=max_age)
    except BadSignature:
        return None


async def get_current_user(
    portal_session: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not portal_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    data = unsign_value(portal_session)
    if not data or "user_id" not in data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = await db.get(User, data["user_id"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user
