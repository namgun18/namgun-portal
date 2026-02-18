"""Authentik OIDC client with PKCE support."""

import hashlib
import secrets
import base64
from urllib.parse import urlencode

import httpx

from app.config import get_settings

settings = get_settings()

# OIDC endpoints derived from issuer
AUTHORIZE_URL = "https://auth.namgun.or.kr/application/o/authorize/"
TOKEN_URL = "https://auth.namgun.or.kr/application/o/token/"
USERINFO_URL = "https://auth.namgun.or.kr/application/o/userinfo/"
END_SESSION_URL = "https://auth.namgun.or.kr/application/o/portal/end-session/"


def generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


def build_authorize_url(state: str, code_challenge: str) -> str:
    """Build Authentik authorization URL with PKCE."""
    params = {
        "response_type": "code",
        "client_id": settings.oidc_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
        "scope": "openid profile email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(code: str, code_verifier: str) -> dict:
    """Exchange authorization code for tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.oidc_redirect_uri,
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
                "code_verifier": code_verifier,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_userinfo(access_token: str) -> dict:
    """Fetch user info from Authentik."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
