"""Admin API routes: user approval, management, analytics."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, and_, case, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.models import AccessLog, User
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
from app.mail import jmap
from app.admin.schemas import (
    AccessLogEntry,
    AccessLogPage,
    ActiveUser,
    AnalyticsOverview,
    CountryStats,
    DailyVisit,
    GitActivityItem,
    GitStats,
    RecentLogin,
    ServiceUsage,
    TopPage,
)

logger = logging.getLogger(__name__)

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

    # Send welcome email to trigger Stalwart mailbox creation
    jmap.clear_cache()
    try:
        await _send_welcome_email(user.email, user.username)
        logger.info("Welcome email sent to %s, waiting for mailbox creation", user.email)
    except Exception as e:
        logger.warning("Failed to send welcome email to %s: %s", user.email, e)

    # Wait for Stalwart to process the email and create the principal
    mail_ready = False
    for attempt in range(5):
        await asyncio.sleep(2)
        jmap.clear_cache()
        account_id = await jmap.resolve_account_id(user.email)
        if account_id:
            mail_ready = True
            logger.info("Mail account ready for %s (account_id=%s)", user.username, account_id)
            break

    msg = f"{user.username} 사용자가 승인되었습니다"
    if not mail_ready:
        msg += " (메일 계정 생성에 시간이 걸릴 수 있습니다)"

    return {"message": msg}


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


# ── Analytics helpers ──────────────────────────────────────


def _period_start(period: str) -> datetime:
    now = datetime.now(timezone.utc)
    if period == "7d":
        return now - timedelta(days=7)
    if period == "30d":
        return now - timedelta(days=30)
    # today
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


# ── GET /api/admin/analytics/overview ─────────────────────


@router.get("/analytics/overview", response_model=AnalyticsOverview)
async def analytics_overview(
    period: str = Query("today", pattern="^(today|7d|30d)$"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    since = _period_start(period)
    result = await db.execute(
        select(
            func.count(AccessLog.id),
            func.count(distinct(AccessLog.ip_address)),
            func.count(case((AccessLog.user_id.isnot(None), 1))),
            func.count(case((AccessLog.user_id.is_(None), 1))),
            func.coalesce(func.avg(AccessLog.response_time_ms), 0),
        ).where(AccessLog.created_at >= since)
    )
    row = result.one()
    return AnalyticsOverview(
        total_visits=row[0],
        unique_ips=row[1],
        authenticated_visits=row[2],
        unauthenticated_visits=row[3],
        avg_response_time_ms=int(row[4]),
    )


# ── GET /api/admin/analytics/daily-visits ─────────────────


@router.get("/analytics/daily-visits", response_model=list[DailyVisit])
async def analytics_daily_visits(
    days: int = Query(30, ge=1, le=90),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    date_col = func.date(AccessLog.created_at)
    result = await db.execute(
        select(
            date_col.label("date"),
            func.count(AccessLog.id),
            func.count(case((AccessLog.user_id.isnot(None), 1))),
            func.count(case((AccessLog.user_id.is_(None), 1))),
        )
        .where(AccessLog.created_at >= since)
        .group_by(date_col)
        .order_by(date_col)
    )
    return [
        DailyVisit(date=str(row[0]), total=row[1], authenticated=row[2], unauthenticated=row[3])
        for row in result.all()
    ]


# ── GET /api/admin/analytics/top-pages ────────────────────


@router.get("/analytics/top-pages", response_model=list[TopPage])
async def analytics_top_pages(
    period: str = Query("today", pattern="^(today|7d|30d)$"),
    limit: int = Query(10, ge=1, le=50),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    since = _period_start(period)
    result = await db.execute(
        select(AccessLog.path, func.count(AccessLog.id).label("cnt"))
        .where(AccessLog.created_at >= since)
        .group_by(AccessLog.path)
        .order_by(func.count(AccessLog.id).desc())
        .limit(limit)
    )
    return [TopPage(path=row[0], count=row[1]) for row in result.all()]


# ── GET /api/admin/analytics/countries ────────────────────


@router.get("/analytics/countries", response_model=list[CountryStats])
async def analytics_countries(
    period: str = Query("today", pattern="^(today|7d|30d)$"),
    limit: int = Query(15, ge=1, le=50),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    since = _period_start(period)
    result = await db.execute(
        select(
            AccessLog.country_code,
            AccessLog.country_name,
            func.count(AccessLog.id).label("cnt"),
        )
        .where(and_(AccessLog.created_at >= since, AccessLog.country_code.isnot(None)))
        .group_by(AccessLog.country_code, AccessLog.country_name)
        .order_by(func.count(AccessLog.id).desc())
        .limit(limit)
    )
    return [
        CountryStats(country_code=row[0], country_name=row[1], count=row[2])
        for row in result.all()
    ]


# ── GET /api/admin/analytics/service-usage ────────────────


@router.get("/analytics/service-usage", response_model=list[ServiceUsage])
async def analytics_service_usage(
    period: str = Query("today", pattern="^(today|7d|30d)$"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    since = _period_start(period)
    result = await db.execute(
        select(AccessLog.service, func.count(AccessLog.id).label("cnt"))
        .where(and_(AccessLog.created_at >= since, AccessLog.service.isnot(None)))
        .group_by(AccessLog.service)
        .order_by(func.count(AccessLog.id).desc())
    )
    return [ServiceUsage(service=row[0], count=row[1]) for row in result.all()]


# ── GET /api/admin/analytics/active-users ─────────────────


@router.get("/analytics/active-users", response_model=list[ActiveUser])
async def analytics_active_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    # Subquery: latest log per user in last 5 min
    subq = (
        select(
            AccessLog.user_id,
            func.max(AccessLog.created_at).label("last_seen"),
        )
        .where(and_(AccessLog.created_at >= since, AccessLog.user_id.isnot(None)))
        .group_by(AccessLog.user_id)
        .subquery()
    )
    result = await db.execute(
        select(
            subq.c.user_id,
            User.username,
            User.display_name,
            AccessLog.path,
            AccessLog.ip_address,
            AccessLog.country_code,
            subq.c.last_seen,
        )
        .join(AccessLog, and_(
            AccessLog.user_id == subq.c.user_id,
            AccessLog.created_at == subq.c.last_seen,
        ))
        .join(User, User.id == subq.c.user_id)
        .order_by(subq.c.last_seen.desc())
    )
    return [
        ActiveUser(
            user_id=row[0], username=row[1], display_name=row[2],
            path=row[3], ip_address=row[4], country_code=row[5],
            last_seen=row[6].isoformat() if row[6] else "",
        )
        for row in result.all()
    ]


# ── GET /api/admin/analytics/recent-logins ────────────────


@router.get("/analytics/recent-logins", response_model=list[RecentLogin])
async def analytics_recent_logins(
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            AccessLog.user_id,
            User.username,
            User.display_name,
            AccessLog.ip_address,
            AccessLog.country_code,
            AccessLog.country_name,
            AccessLog.created_at,
        )
        .join(User, User.id == AccessLog.user_id)
        .where(and_(
            AccessLog.path.in_(["/api/auth/login", "/api/auth/callback"]),
            AccessLog.status_code < 400,
        ))
        .order_by(AccessLog.created_at.desc())
        .limit(limit)
    )
    return [
        RecentLogin(
            user_id=row[0], username=row[1], display_name=row[2],
            ip_address=row[3], country_code=row[4], country_name=row[5],
            login_at=row[6].isoformat() if row[6] else "",
        )
        for row in result.all()
    ]


# ── GET /api/admin/analytics/access-logs ──────────────────


@router.get("/analytics/access-logs", response_model=AccessLogPage)
async def analytics_access_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    service: str | None = Query(None),
    user_id: str | None = Query(None),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if service:
        conditions.append(AccessLog.service == service)
    if user_id:
        conditions.append(AccessLog.user_id == user_id)

    where = and_(*conditions) if conditions else True

    # Count
    count_result = await db.execute(
        select(func.count(AccessLog.id)).where(where)
    )
    total = count_result.scalar() or 0

    # Fetch with LEFT JOIN to get username
    offset = (page - 1) * limit
    result = await db.execute(
        select(
            AccessLog.id,
            AccessLog.ip_address,
            AccessLog.method,
            AccessLog.path,
            AccessLog.status_code,
            AccessLog.response_time_ms,
            AccessLog.browser,
            AccessLog.os,
            AccessLog.device,
            AccessLog.country_code,
            AccessLog.country_name,
            AccessLog.user_id,
            User.username,
            AccessLog.service,
            AccessLog.created_at,
        )
        .outerjoin(User, User.id == AccessLog.user_id)
        .where(where)
        .order_by(AccessLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    logs = [
        AccessLogEntry(
            id=row[0], ip_address=row[1], method=row[2], path=row[3],
            status_code=row[4], response_time_ms=row[5],
            browser=row[6], os=row[7], device=row[8],
            country_code=row[9], country_name=row[10],
            user_id=row[11], username=row[12],
            service=row[13],
            created_at=row[14].isoformat() if row[14] else "",
        )
        for row in result.all()
    ]
    return AccessLogPage(logs=logs, total=total, page=page, limit=limit)


# ── GET /api/admin/analytics/git-activity ─────────────────


@router.get("/analytics/git-activity", response_model=list[GitActivityItem])
async def analytics_git_activity(
    admin: User = Depends(require_admin),
):
    from app.git import gitea
    try:
        repos, _ = await gitea.search_repos(limit=10, sort="updated")
    except Exception:
        return []

    items: list[GitActivityItem] = []
    for repo in repos[:5]:
        owner = repo.get("owner", {}).get("login", "")
        name = repo.get("name", "")
        full = repo.get("full_name", f"{owner}/{name}")

        # Recent commits (as push events)
        try:
            commits = await gitea.get_commits(owner, name, page=1)
            for c in commits[:3]:
                commit_info = c.get("commit", {})
                items.append(GitActivityItem(
                    repo_name=name, repo_full_name=full,
                    event_type="push",
                    title=commit_info.get("message", "").split("\n")[0][:100],
                    user=commit_info.get("author", {}).get("name", ""),
                    created_at=commit_info.get("author", {}).get("date", ""),
                ))
        except Exception:
            pass

        # Recent issues
        try:
            issues = await gitea.get_issues(owner, name, state="all", page=1)
            for iss in issues[:2]:
                items.append(GitActivityItem(
                    repo_name=name, repo_full_name=full,
                    event_type="issue",
                    title=iss.get("title", "")[:100],
                    user=iss.get("user", {}).get("login", ""),
                    created_at=iss.get("created_at", ""),
                ))
        except Exception:
            pass

        # Recent PRs
        try:
            pulls = await gitea.get_pulls(owner, name, state="all", page=1)
            for pr in pulls[:2]:
                items.append(GitActivityItem(
                    repo_name=name, repo_full_name=full,
                    event_type="pull_request",
                    title=pr.get("title", "")[:100],
                    user=pr.get("user", {}).get("login", ""),
                    created_at=pr.get("created_at", ""),
                ))
        except Exception:
            pass

    items.sort(key=lambda x: x.created_at, reverse=True)
    return items[:20]


# ── GET /api/admin/analytics/git-stats ────────────────────


@router.get("/analytics/git-stats", response_model=GitStats)
async def analytics_git_stats(
    admin: User = Depends(require_admin),
):
    from app.git import gitea
    try:
        repos, total_repos = await gitea.search_repos(limit=50, sort="updated")
        total_issues = sum(r.get("open_issues_count", 0) for r in repos)
        total_pulls = sum(r.get("open_pr_counter", 0) for r in repos)
        # Unique owners as proxy for users
        users = {r.get("owner", {}).get("login") for r in repos}
        return GitStats(
            total_repos=total_repos,
            total_users=len(users),
            total_issues=total_issues,
            total_pulls=total_pulls,
        )
    except Exception:
        return GitStats(total_repos=0, total_users=0, total_issues=0, total_pulls=0)


# ── Email helper ──────────────────────────────────────────


async def _send_welcome_email(to_email: str, username: str) -> None:
    """Send welcome email via SMTP to trigger Stalwart mailbox creation."""
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(
        f"{username}님, namgun.or.kr 포털 가입이 승인되었습니다.\n\n"
        f"이제 포털(https://namgun.or.kr)에 로그인하여 메일, 파일, "
        f"회의 등 모든 서비스를 이용하실 수 있습니다.\n\n"
        f"— namgun.or.kr 관리팀",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "[namgun.or.kr] 가입이 승인되었습니다"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email

    def _do_send():
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)

    await asyncio.to_thread(_do_send)
