"""Portal OIDC provider — exposes authorize/token/userinfo for Gitea etc."""

import base64
import hashlib
import json
import secrets
import time

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode, quote

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.auth.deps import SESSION_COOKIE, unsign_value
from app.auth.oauth_store import (
    CODE_TTL,
    AuthorizationCode,
    consume_code,
    store_code,
)

settings = get_settings()
router = APIRouter(prefix="/oauth", tags=["oauth-provider"])

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = 3600  # 1 hour


# ── Helpers ──────────────────────────────────────────────────


def _get_clients() -> dict:
    return json.loads(settings.oauth_clients_json)


def _create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iss": settings.app_url,
        "iat": int(time.time()),
        "exp": int(time.time()) + ACCESS_TOKEN_TTL,
        "type": "portal_oauth",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def _verify_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])


def _parse_basic_auth(header: str) -> tuple[str, str] | None:
    if not header.startswith("Basic "):
        return None
    try:
        decoded = base64.b64decode(header[6:]).decode()
        client_id, client_secret = decoded.split(":", 1)
        return client_id, client_secret
    except Exception:
        return None


# ── OIDC Discovery ───────────────────────────────────────────


@router.get("/.well-known/openid-configuration")
async def openid_configuration():
    base = settings.app_url
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "userinfo_endpoint": f"{base}/oauth/userinfo",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": [JWT_ALGORITHM],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
        ],
    }


# ── Authorization Endpoint ───────────────────────────────────


@router.get("/authorize")
async def authorize(
    request: Request,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    state: str = "",
    scope: str = "openid",
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
    portal_session: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    # Validate client
    clients = _get_clients()
    client_cfg = clients.get(client_id)
    if not client_cfg:
        raise HTTPException(status_code=400, detail="Unknown client")

    if redirect_uri not in client_cfg.get("redirect_uris", []):
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type")

    # Check portal session
    current_url = f"/oauth/authorize?{request.url.query}"

    if not portal_session:
        return RedirectResponse(
            url=f"/login?redirect={quote(current_url)}", status_code=302
        )

    data = unsign_value(portal_session)
    if not data or "user_id" not in data:
        return RedirectResponse(
            url=f"/login?redirect={quote(current_url)}", status_code=302
        )

    user = await db.get(User, data["user_id"])
    if not user or not user.is_active:
        return RedirectResponse(
            url=f"/login?redirect={quote(current_url)}", status_code=302
        )

    # Generate authorization code
    code = secrets.token_urlsafe(32)
    store_code(
        code,
        AuthorizationCode(
            user_id=user.id,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            expires_at=time.time() + CODE_TTL,
        ),
    )

    params = {"code": code}
    if state:
        params["state"] = state
    return RedirectResponse(
        url=f"{redirect_uri}?{urlencode(params)}", status_code=302
    )


# ── Token Endpoint ───────────────────────────────────────────


@router.post("/token")
async def token(request: Request):
    # Parse body (form-encoded per OAuth spec)
    form = await request.form()
    data = dict(form)

    grant_type = data.get("grant_type")
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")

    code = data.get("code", "")
    redirect_uri = data.get("redirect_uri", "")
    client_id = data.get("client_id", "")
    client_secret = data.get("client_secret", "")
    code_verifier = data.get("code_verifier")

    # Support Basic auth header
    if not client_id or not client_secret:
        auth_header = request.headers.get("authorization", "")
        parsed = _parse_basic_auth(auth_header)
        if parsed:
            client_id, client_secret = parsed

    # Validate client credentials
    clients = _get_clients()
    client_cfg = clients.get(client_id)
    if not client_cfg or client_cfg.get("secret") != client_secret:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    # Consume authorization code (one-time)
    auth_code = consume_code(code)
    if not auth_code:
        raise HTTPException(status_code=400, detail="Code expired or invalid")

    if auth_code.client_id != client_id:
        raise HTTPException(status_code=400, detail="Client mismatch")

    if auth_code.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    # PKCE verification
    if auth_code.code_challenge and code_verifier:
        digest = hashlib.sha256(code_verifier.encode()).digest()
        computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        if computed != auth_code.code_challenge:
            raise HTTPException(status_code=400, detail="Invalid code_verifier")

    access_token = _create_access_token(auth_code.user_id)

    return JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_TOKEN_TTL,
        }
    )


# ── UserInfo Endpoint ────────────────────────────────────────


@router.get("/userinfo")
async def userinfo(request: Request, db: AsyncSession = Depends(get_db)):
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = _verify_access_token(auth_header[7:])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "sub": user.id,
        "preferred_username": user.username,
        "name": user.display_name or user.username,
        "email": user.email,
        "groups": ["admin"] if user.is_admin else [],
    }
