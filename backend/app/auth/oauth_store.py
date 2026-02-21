"""In-memory authorization code store for Portal OIDC provider."""

import time
from dataclasses import dataclass

CODE_TTL = 300  # 5 minutes


@dataclass
class AuthorizationCode:
    user_id: str
    client_id: str
    redirect_uri: str
    scope: str
    code_challenge: str | None
    nonce: str | None
    expires_at: float


_codes: dict[str, AuthorizationCode] = {}


def store_code(code: str, data: AuthorizationCode) -> None:
    _cleanup()
    _codes[code] = data


def consume_code(code: str) -> AuthorizationCode | None:
    """Return and remove code (one-time use). Returns None if expired/missing."""
    _cleanup()
    return _codes.pop(code, None)


def _cleanup() -> None:
    now = time.time()
    expired = [k for k, v in _codes.items() if v.expires_at < now]
    for k in expired:
        del _codes[k]
