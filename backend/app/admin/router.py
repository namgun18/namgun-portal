"""Admin API routes: user approval, management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.config import get_settings
from app.auth.authentik_admin import (
    AuthentikAdminError,
    activate_user,
    add_user_to_group,
    deactivate_user,
    delete_user,
    lookup_pk_by_username,
    remove_user_from_group,
)

settings = get_settings()

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Dependency: admin-only ───────────────────────────────────


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    return user


# ── Response schemas ─────────────────────────────────────────


class AdminUserResponse(BaseModel):
    id: str
    username: str
    display_name: str | None
    email: str | None
    recovery_email: str | None
    is_admin: bool
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


# ── GET /api/admin/users — 전체 사용자 목록 ──────────────────


@router.get("/users")
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "email": u.email,
            "recovery_email": u.recovery_email,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


# ── GET /api/admin/users/pending — 승인 대기 목록 ────────────


@router.get("/users/pending")
async def list_pending_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List users pending approval."""
    result = await db.execute(
        select(User).where(User.is_active == False).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "email": u.email,
            "recovery_email": u.recovery_email,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


# ── POST /api/admin/users/{user_id}/approve — 승인 ──────────


@router.post("/users/{user_id}/approve")
async def approve_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending user registration."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    if user.is_active:
        raise HTTPException(status_code=400, detail="이미 활성화된 사용자입니다")

    # Resolve Authentik PK if not cached
    pk = user.authentik_pk
    if not pk:
        pk = await lookup_pk_by_username(user.username)
        if pk:
            user.authentik_pk = pk

    if not pk:
        raise HTTPException(status_code=404, detail="Authentik 사용자를 찾을 수 없습니다")

    # Activate in Authentik
    try:
        await activate_user(pk)
    except AuthentikAdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Activate in portal DB
    user.is_active = True
    await db.commit()

    return {"message": f"{user.username} 사용자가 승인되었습니다"}


# ── POST /api/admin/users/{user_id}/reject — 거절 ───────────


@router.post("/users/{user_id}/reject")
async def reject_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reject a pending user registration (deletes from Authentik and portal)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # Delete from Authentik
    pk = user.authentik_pk or await lookup_pk_by_username(user.username)
    if pk:
        try:
            await delete_user(pk)
        except AuthentikAdminError:
            pass  # May already be deleted

    # Delete from portal DB
    await db.delete(user)
    await db.commit()

    return {"message": "가입 신청이 거절되었습니다"}


# ── POST /api/admin/users/{user_id}/deactivate — 비활성화 ───


@router.post("/users/{user_id}/deactivate")
async def deactivate_user_endpoint(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate an active user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="이미 비활성화된 사용자입니다")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="자기 자신은 비활성화할 수 없습니다")

    # Resolve Authentik PK
    pk = user.authentik_pk
    if not pk:
        pk = await lookup_pk_by_username(user.username)
        if pk:
            user.authentik_pk = pk

    if not pk:
        raise HTTPException(status_code=404, detail="Authentik 사용자를 찾을 수 없습니다")

    # Deactivate in Authentik
    try:
        await deactivate_user(pk)
    except AuthentikAdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Deactivate in portal DB
    user.is_active = False
    await db.commit()

    return {"message": f"{user.username} 사용자가 비활성화되었습니다"}


# ── POST /api/admin/users/{user_id}/set-role — 권한 변경 ──


class SetRoleRequest(BaseModel):
    is_admin: bool


@router.post("/users/{user_id}/set-role")
async def set_user_role(
    user_id: str,
    body: SetRoleRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Grant or revoke admin role for a user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="자기 자신의 권한은 변경할 수 없습니다")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="비활성 사용자의 권한은 변경할 수 없습니다")
    if user.is_admin == body.is_admin:
        role = "관리자" if body.is_admin else "일반 사용자"
        raise HTTPException(status_code=400, detail=f"이미 {role}입니다")

    # Resolve Authentik PK
    pk = user.authentik_pk
    if not pk:
        pk = await lookup_pk_by_username(user.username)
        if pk:
            user.authentik_pk = pk

    if not pk:
        raise HTTPException(status_code=404, detail="Authentik 사용자를 찾을 수 없습니다")

    admins_group = settings.authentik_admins_group_pk
    if not admins_group:
        raise HTTPException(status_code=500, detail="관리자 그룹이 설정되지 않았습니다")

    # Update Authentik group membership
    try:
        if body.is_admin:
            await add_user_to_group(pk, admins_group)
        else:
            await remove_user_from_group(pk, admins_group)
    except AuthentikAdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Update portal DB
    user.is_admin = body.is_admin
    await db.commit()

    role = "관리자" if body.is_admin else "일반 사용자"
    return {"message": f"{user.username} 사용자가 {role}(으)로 변경되었습니다"}
