"""File browser API endpoints."""

import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.config import get_settings
from app.db.models import ShareLink, User
from app.db.session import get_db
from app.files import preview as pv
from app.files import service as fs
from app.files.schemas import (
    FileListResponse,
    MkdirRequest,
    MoveRequest,
    RenameRequest,
    ShareLinkCreate,
    ShareLinkListItem,
    ShareLinkResponse,
    StorageInfo,
)

router = APIRouter(prefix="/api/files", tags=["files"])
settings = get_settings()

EXPIRES_MAP = {"1h": 1, "1d": 24, "7d": 168}  # hours


# ─── Helpers ───


def _check_path(virtual_path: str, user: User) -> Path:
    """Resolve + enforce security. Returns real Path or raises HTTP error."""
    try:
        return fs.resolve_path(virtual_path, user)
    except fs.PathSecurityError:
        raise HTTPException(status_code=403, detail="Path traversal blocked")
    except fs.AccessDeniedError:
        raise HTTPException(status_code=403, detail="Access denied")


# ─── Directory listing ───


@router.get("/list", response_model=FileListResponse)
async def list_files(
    path: str = Query("my/", description="Virtual path"),
    user: User = Depends(get_current_user),
):
    vp = path.strip("/")

    # Root listing: return virtual roots
    if not vp or vp in ("", "."):
        roots = [
            {"name": "내 파일", "path": "my", "is_dir": True, "size": 0, "modified_at": None, "mime_type": None},
            {"name": "공유 파일", "path": "shared", "is_dir": True, "size": 0, "modified_at": None, "mime_type": None},
        ]
        if user.is_admin:
            roots.append(
                {"name": "전체 사용자", "path": "users", "is_dir": True, "size": 0, "modified_at": None, "mime_type": None}
            )
        return FileListResponse(path="", items=roots)

    # Ensure user directory exists for "my" paths
    if vp == "my" or vp.startswith("my/"):
        fs.ensure_user_dir(user)
    if vp == "shared" or vp.startswith("shared/"):
        fs.ensure_shared_dir()

    real = _check_path(vp, user)
    if not real.exists():
        real.mkdir(parents=True, exist_ok=True)

    items = fs.list_directory(real, vp)
    return FileListResponse(path=vp, items=items)


# ─── Download ───


@router.get("/download")
async def download_file(
    path: str = Query(...),
    user: User = Depends(get_current_user),
):
    real = _check_path(path, user)
    if not real.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(real),
        filename=real.name,
        media_type="application/octet-stream",
    )


# ─── Upload ───


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    path: str = Query("my/", description="Target directory virtual path"),
    user: User = Depends(get_current_user),
):
    max_bytes = settings.upload_max_size_mb * 1024 * 1024

    vp = path.strip("/")
    if not vp:
        vp = "my"

    # Ensure dirs
    if vp == "my" or vp.startswith("my/"):
        fs.ensure_user_dir(user)
    if vp == "shared" or vp.startswith("shared/"):
        fs.ensure_shared_dir()

    real_dir = _check_path(vp, user)
    real_dir.mkdir(parents=True, exist_ok=True)

    if not real_dir.is_dir():
        raise HTTPException(status_code=400, detail="Target is not a directory")

    target = real_dir / file.filename
    if "/" in file.filename or "\\" in file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Stream write with size check
    written = 0
    with open(target, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                f.close()
                target.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds {settings.upload_max_size_mb}MB limit",
                )
            f.write(chunk)

    return {"ok": True, "name": file.filename, "size": written}


# ─── Mkdir ───


@router.post("/mkdir")
async def mkdir(body: MkdirRequest, user: User = Depends(get_current_user)):
    vp = body.path.strip("/")
    parent_vp = "/".join(vp.rsplit("/", 1)[:-1]) if "/" in vp else vp.split("/")[0]
    new_name = vp.rsplit("/", 1)[-1] if "/" in vp else ""

    if not new_name:
        raise HTTPException(status_code=400, detail="Invalid path for mkdir")

    # Ensure base dirs
    if parent_vp == "my" or parent_vp.startswith("my/"):
        fs.ensure_user_dir(user)

    parent_real = _check_path(parent_vp, user)
    parent_real.mkdir(parents=True, exist_ok=True)

    target = parent_real / new_name
    if target.exists():
        raise HTTPException(status_code=409, detail="Already exists")

    target.mkdir(parents=True)
    return {"ok": True, "path": vp}


# ─── Delete ───


@router.delete("/delete")
async def delete_file(
    path: str = Query(...),
    user: User = Depends(get_current_user),
):
    real = _check_path(path, user)
    if not real.exists():
        raise HTTPException(status_code=404, detail="Not found")

    fs.delete_path(real)
    return {"ok": True}


# ─── Rename ───


@router.patch("/rename")
async def rename_file(body: RenameRequest, user: User = Depends(get_current_user)):
    real = _check_path(body.path, user)
    if not real.exists():
        raise HTTPException(status_code=404, detail="Not found")

    try:
        new_path = fs.rename_path(real, body.new_name)
    except fs.PathSecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {"ok": True, "new_name": new_path.name}


# ─── Move / Copy ───


@router.patch("/move")
async def move_file(body: MoveRequest, user: User = Depends(get_current_user)):
    src_real = _check_path(body.src, user)
    if not src_real.exists():
        raise HTTPException(status_code=404, detail="Source not found")

    dst_real = _check_path(body.dst, user)
    dst_real.mkdir(parents=True, exist_ok=True)

    try:
        fs.move_path(src_real, dst_real, copy=body.copy)
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {"ok": True}


# ─── Preview ───


@router.get("/preview")
async def preview_file(
    path: str = Query(...),
    user: User = Depends(get_current_user),
):
    real = _check_path(path, user)
    if not real.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    ptype = pv.can_preview(real)
    if not ptype:
        raise HTTPException(status_code=415, detail="Preview not supported")

    if ptype == "image":
        if real.suffix.lower() == ".svg":
            data = real.read_bytes()
            return Response(content=data, media_type="image/svg+xml")
        data = pv.generate_thumbnail(real)
        if not data:
            raise HTTPException(status_code=500, detail="Thumbnail generation failed")
        return Response(content=data, media_type="image/jpeg")

    if ptype == "text":
        text = pv.get_text_preview(real)
        return {"type": "text", "content": text, "name": real.name}

    if ptype == "pdf":
        return FileResponse(path=str(real), media_type="application/pdf")

    raise HTTPException(status_code=415)


# ─── Storage info ───


@router.get("/info", response_model=StorageInfo)
async def storage_info(user: User = Depends(get_current_user)):
    fs.ensure_user_dir(user)
    personal = fs.get_dir_size(Path(settings.storage_root) / "users" / user.id)
    shared = fs.get_dir_size(Path(settings.storage_root) / "shared")
    return StorageInfo(personal_used=personal, shared_used=shared, total_available=0)


# ─── Share links ───


@router.post("/share", response_model=ShareLinkResponse)
async def create_share_link(
    body: ShareLinkCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    real = _check_path(body.path, user)
    if not real.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    token = secrets.token_urlsafe(32)

    expires_at = None
    if body.expires_in and body.expires_in in EXPIRES_MAP:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=EXPIRES_MAP[body.expires_in])

    max_downloads = 1 if body.one_time else None

    link = ShareLink(
        token=token,
        file_path=str(real),
        display_name=real.name,
        created_by=user.id,
        expires_at=expires_at,
        max_downloads=max_downloads,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    url = f"{settings.app_url}/api/files/shared/{token}"
    return ShareLinkResponse(
        token=token,
        url=url,
        display_name=link.display_name,
        expires_at=link.expires_at,
        max_downloads=link.max_downloads,
        created_at=link.created_at,
    )


@router.get("/share/list", response_model=list[ShareLinkListItem])
async def list_share_links(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ShareLink).where(ShareLink.created_by == user.id).order_by(ShareLink.created_at.desc())
    result = await db.execute(stmt)
    links = result.scalars().all()
    return [
        ShareLinkListItem(
            id=l.id,
            token=l.token,
            display_name=l.display_name,
            file_path=l.file_path,
            expires_at=l.expires_at,
            max_downloads=l.max_downloads,
            download_count=l.download_count,
            created_at=l.created_at,
        )
        for l in links
    ]


@router.delete("/share/{link_id}")
async def delete_share_link(
    link_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await db.get(ShareLink, link_id)
    if not link or (link.created_by != user.id and not user.is_admin):
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(link)
    await db.commit()
    return {"ok": True}


# ─── Public shared download (no auth) ───


@router.get("/shared/{token}")
async def download_shared(token: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ShareLink).where(ShareLink.token == token)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found or expired")

    # Check expiry
    if link.expires_at and datetime.now(timezone.utc) > link.expires_at:
        raise HTTPException(status_code=404, detail="Link expired")

    # Check download limit
    if link.max_downloads is not None and link.download_count >= link.max_downloads:
        raise HTTPException(status_code=404, detail="Download limit reached")

    real = Path(link.file_path)
    if not real.is_file():
        raise HTTPException(status_code=404, detail="File no longer exists")

    # Increment download count
    link.download_count += 1
    await db.commit()

    return FileResponse(
        path=str(real),
        filename=link.display_name,
        media_type="application/octet-stream",
    )
