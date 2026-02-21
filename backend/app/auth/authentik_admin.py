"""Authentik Admin API client for user management."""

import httpx

from app.config import get_settings


class AuthentikAdminError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


settings = get_settings()


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.authentik_api_token}"}


def _api(path: str) -> str:
    return f"{settings.authentik_base_url}{path}"


async def create_user(
    username: str, email: str, name: str, password: str, recovery_email: str
) -> dict:
    """Create an inactive user in Authentik and set password.

    Returns user data including 'uid' (OIDC sub) and 'pk' (Admin API ID).
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _api("/api/v3/core/users/"),
            headers=_headers(),
            json={
                "username": username,
                "email": email,
                "name": name,
                "is_active": False,
                "attributes": {"recovery_email": recovery_email},
            },
        )
        if resp.status_code == 400:
            data = resp.json()
            errors = data if isinstance(data, dict) else {}
            if "username" in errors:
                raise AuthentikAdminError("이미 사용 중인 사용자명입니다")
            if "email" in errors:
                raise AuthentikAdminError("이미 사용 중인 이메일입니다")
            raise AuthentikAdminError(f"사용자 생성 실패: {resp.text}")
        if resp.status_code != 201:
            raise AuthentikAdminError(
                f"사용자 생성 실패: {resp.status_code}", status_code=502
            )

        user_data = resp.json()
        user_pk = user_data["pk"]

        # Set password
        pwd_resp = await client.post(
            _api(f"/api/v3/core/users/{user_pk}/set_password/"),
            headers=_headers(),
            json={"password": password},
        )
        if pwd_resp.status_code not in (200, 204):
            await client.delete(
                _api(f"/api/v3/core/users/{user_pk}/"), headers=_headers()
            )
            raise AuthentikAdminError("비밀번호 설정 실패", status_code=502)

        # Add to Users group
        if settings.authentik_users_group_pk:
            await client.post(
                _api(
                    f"/api/v3/core/groups/{settings.authentik_users_group_pk}/add_user/"
                ),
                headers=_headers(),
                json={"pk": user_pk},
            )

        return user_data


async def activate_user(pk: int) -> dict:
    """Activate a user (admin approval)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.patch(
            _api(f"/api/v3/core/users/{pk}/"),
            headers=_headers(),
            json={"is_active": True},
        )
        if resp.status_code != 200:
            raise AuthentikAdminError("사용자 활성화 실패", status_code=502)
        return resp.json()


async def deactivate_user(pk: int) -> dict:
    """Deactivate a user."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.patch(
            _api(f"/api/v3/core/users/{pk}/"),
            headers=_headers(),
            json={"is_active": False},
        )
        if resp.status_code != 200:
            raise AuthentikAdminError("사용자 비활성화 실패", status_code=502)
        return resp.json()


async def update_user(pk: int, **fields) -> dict:
    """Update user fields in Authentik."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.patch(
            _api(f"/api/v3/core/users/{pk}/"),
            headers=_headers(),
            json=fields,
        )
        if resp.status_code != 200:
            raise AuthentikAdminError("사용자 정보 수정 실패", status_code=502)
        return resp.json()


async def set_password(pk: int, password: str) -> None:
    """Set user password in Authentik."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _api(f"/api/v3/core/users/{pk}/set_password/"),
            headers=_headers(),
            json={"password": password},
        )
        if resp.status_code not in (200, 204):
            raise AuthentikAdminError("비밀번호 변경 실패", status_code=502)


async def delete_user(pk: int) -> None:
    """Delete a user from Authentik."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.delete(
            _api(f"/api/v3/core/users/{pk}/"), headers=_headers()
        )
        if resp.status_code not in (200, 204):
            raise AuthentikAdminError("사용자 삭제 실패", status_code=502)


async def get_recovery_link(pk: int) -> str:
    """Generate a password recovery link via Authentik."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _api(f"/api/v3/core/users/{pk}/recovery/"),
            headers=_headers(),
        )
        if resp.status_code != 200:
            raise AuthentikAdminError("복구 링크 생성 실패", status_code=502)
        return resp.json().get("link", "")


async def add_user_to_group(user_pk: int, group_pk: str) -> None:
    """Add a user to an Authentik group."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _api(f"/api/v3/core/groups/{group_pk}/add_user/"),
            headers=_headers(),
            json={"pk": user_pk},
        )
        if resp.status_code not in (200, 204):
            raise AuthentikAdminError("그룹 추가 실패", status_code=502)


async def remove_user_from_group(user_pk: int, group_pk: str) -> None:
    """Remove a user from an Authentik group."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _api(f"/api/v3/core/groups/{group_pk}/remove_user/"),
            headers=_headers(),
            json={"pk": user_pk},
        )
        if resp.status_code not in (200, 204):
            raise AuthentikAdminError("그룹 제거 실패", status_code=502)


async def lookup_pk_by_username(username: str) -> int | None:
    """Look up Authentik PK by username."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            _api("/api/v3/core/users/"),
            headers=_headers(),
            params={"username": username},
        )
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return results[0]["pk"]
    return None
