"""Authentik OIDC client — server-side authentication via Flow Executor API."""

import hashlib
import secrets
import base64
from urllib.parse import urlencode, urlparse, parse_qs

import httpx

from app.config import get_settings


class AuthenticationError(Exception):
    """Raised when Authentik authentication fails."""

    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


settings = get_settings()

# OIDC endpoints (used by fallback redirect flow & token exchange)
AUTHORIZE_URL = f"{settings.authentik_base_url}/application/o/authorize/"
TOKEN_URL = f"{settings.authentik_base_url}/application/o/token/"
USERINFO_URL = f"{settings.authentik_base_url}/application/o/userinfo/"
END_SESSION_URL = f"{settings.authentik_base_url}/application/o/portal/end-session/"


# ── PKCE helpers ──────────────────────────────────────────────


def generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


# ── Redirect-flow helpers (fallback) ─────────────────────────


def build_authorize_url(state: str, code_challenge: str) -> str:
    """Build Authentik authorization URL with PKCE (redirect flow)."""
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


async def exchange_code(
    code: str, code_verifier: str, redirect_uri: str | None = None
) -> dict:
    """Exchange authorization code for tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri or settings.oidc_redirect_uri,
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


# ── Server-side authentication (replaces popup bridge) ───────


async def server_side_authenticate(username: str, password: str) -> dict:
    """Drive the Authentik Flow Executor API and return userinfo dict.

    Steps:
      1. GET /application/o/authorize/  →  register OAuth intent + get session
      2. GET /api/v3/flows/executor/{slug}/  →  fetch first challenge
      3. POST identification stage  →  {uid_field: username}
      4. POST password stage  →  {password: password}
      5. Follow redirect back to authorize  →  obtain authorization code
      6. Exchange code  →  get tokens
      7. Fetch userinfo  →  return
    """
    base = settings.authentik_base_url
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(32)

    auth_params = {
        "response_type": "code",
        "client_id": settings.oidc_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
        "scope": "openid profile email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
        ) as client:
            # Step 1: GET authorize (follow redirects to establish session)
            resp = await client.get(
                f"{base}/application/o/authorize/",
                params=auth_params,
                follow_redirects=True,
            )
            # After following redirects, we land on the flow page (HTML).
            # The session cookies are now set in the client.

            # Step 2: GET Flow Executor API (may redirect once for session init)
            flow_url = (
                f"{base}/api/v3/flows/executor/{settings.authentik_flow_slug}/"
            )
            resp = await client.get(
                flow_url, follow_redirects=True,
            )
            if resp.status_code != 200:
                raise AuthenticationError(
                    "인증 서버 응답이 올바르지 않습니다", status_code=502
                )
            challenge = resp.json()

            # Step 3: Identification stage
            if challenge.get("component") == "ak-stage-identification":
                resp = await client.post(
                    flow_url,
                    json={"uid_field": username},
                    follow_redirects=True,
                )
                if resp.status_code != 200:
                    raise AuthenticationError(
                        "사용자명 또는 비밀번호가 올바르지 않습니다"
                    )
                challenge = resp.json()

            _check_errors(challenge)

            # Step 4: Password stage
            if challenge.get("component") == "ak-stage-password":
                resp = await client.post(
                    flow_url,
                    json={"password": password},
                    follow_redirects=True,
                )
                if resp.status_code != 200:
                    raise AuthenticationError(
                        "사용자명 또는 비밀번호가 올바르지 않습니다"
                    )
                challenge = resp.json()

            _check_errors(challenge)

            # Step 5: Follow redirect → authorize → code
            if challenge.get("type") == "redirect":
                to = challenge.get("to", "")
                if to.startswith("/"):
                    to = f"{base}{to}"
                resp = await client.get(to, follow_redirects=False)
            else:
                # Fallback: re-hit authorize
                resp = await client.get(
                    f"{base}/application/o/authorize/",
                    params=auth_params,
                    follow_redirects=False,
                )

            if resp.status_code not in (302, 303):
                raise AuthenticationError("인증 처리 중 오류가 발생했습니다")

            location = str(resp.headers.get("location", ""))
            return await _finish(location, code_verifier)

    except httpx.ConnectError:
        raise AuthenticationError(
            "인증 서버에 연결할 수 없습니다", status_code=502
        )
    except httpx.TimeoutException:
        raise AuthenticationError(
            "인증 서버 응답 시간이 초과되었습니다", status_code=502
        )


async def _finish(location: str, code_verifier: str) -> dict:
    """Extract code from redirect Location, exchange it, return userinfo."""
    params = parse_qs(urlparse(location).query)
    code = params.get("code", [None])[0]

    if not code:
        error = params.get("error_description", params.get("error", [None]))
        msg = error[0] if error else "인증 코드를 받지 못했습니다"
        raise AuthenticationError(msg)

    tokens = await exchange_code(code, code_verifier)
    return await get_userinfo(tokens["access_token"])


def _check_errors(challenge: dict) -> None:
    """Raise on access-denied, response errors, or unsupported stages."""
    component = challenge.get("component", "")

    if component == "ak-stage-access-denied":
        raise AuthenticationError("사용자명 또는 비밀번호가 올바르지 않습니다")

    if challenge.get("response_errors"):
        raise AuthenticationError("사용자명 또는 비밀번호가 올바르지 않습니다")

    known = (
        "ak-stage-identification",
        "ak-stage-password",
        "ak-stage-autosubmit",
        "xak-flow-redirect",
    )
    if (
        component.startswith("ak-stage-")
        and component not in known
        and challenge.get("type") != "redirect"
    ):
        raise AuthenticationError(
            "지원하지 않는 인증 단계입니다", status_code=400
        )
