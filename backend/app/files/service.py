"""File system operations with path security enforcement."""

import mimetypes
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.db.models import User
from app.files.schemas import FileItem

settings = get_settings()
STORAGE_ROOT = Path(settings.storage_root)

# TTL cache: {real_path_str: (timestamp, [FileItem, ...])}
_dir_cache: dict[str, tuple[float, list[FileItem]]] = {}
_CACHE_TTL = 30  # seconds

# TTL cache for directory sizes: {path_str: (timestamp, size_bytes)}
_size_cache: dict[str, tuple[float, int]] = {}
_SIZE_CACHE_TTL = 60  # seconds


class PathSecurityError(Exception):
    pass


class AccessDeniedError(Exception):
    pass


def _resolve_virtual_path(virtual_path: str, user: User) -> Path:
    """Resolve a virtual path (my/... or shared/...) to a real filesystem path.

    Raises PathSecurityError if path traversal is detected.
    Raises AccessDeniedError if user lacks permission.
    """
    # Normalize and strip leading slashes
    vp = virtual_path.strip("/")
    if not vp:
        raise PathSecurityError("Empty path")

    parts = vp.split("/", 1)
    root_segment = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if root_segment == "my":
        base = STORAGE_ROOT / "users" / user.id
    elif root_segment == "shared":
        base = STORAGE_ROOT / "shared"
    elif root_segment == "users" and user.is_admin:
        # Admin can browse all user directories
        base = STORAGE_ROOT / "users"
        if rest:
            real = (base / rest).resolve()
            if not str(real).startswith(str(base.resolve())):
                raise PathSecurityError("Path traversal detected")
            return real
        return base.resolve()
    else:
        raise AccessDeniedError(f"Unknown root: {root_segment}")

    if rest:
        real = (base / rest).resolve()
    else:
        real = base.resolve()

    # Security: ensure resolved path is within the allowed base
    if not str(real).startswith(str(base.resolve())):
        raise PathSecurityError("Path traversal detected")

    return real


def resolve_path(virtual_path: str, user: User) -> Path:
    """Public wrapper for path resolution."""
    return _resolve_virtual_path(virtual_path, user)


def ensure_user_dir(user: User) -> Path:
    """Ensure user's personal directory exists."""
    user_dir = STORAGE_ROOT / "users" / user.id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def ensure_shared_dir() -> None:
    """Ensure shared directory exists."""
    shared_dir = STORAGE_ROOT / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)


def _scan_directory(real_path: Path, virtual_prefix: str) -> list[FileItem]:
    """Perform actual NFS I/O to list directory contents."""
    items: list[FileItem] = []
    try:
        for entry in sorted(real_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            stat = entry.stat()
            mime = None
            if entry.is_file():
                mime, _ = mimetypes.guess_type(entry.name)

            vpath = f"{virtual_prefix}/{entry.name}".strip("/")
            items.append(
                FileItem(
                    name=entry.name,
                    path=vpath,
                    is_dir=entry.is_dir(),
                    size=stat.st_size if entry.is_file() else 0,
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    mime_type=mime,
                )
            )
    except PermissionError:
        pass
    return items


def list_directory(real_path: Path, virtual_prefix: str) -> list[FileItem]:
    """List contents of a directory (with TTL cache)."""
    if not real_path.is_dir():
        return []

    cache_key = str(real_path.resolve())
    now = time.monotonic()

    cached = _dir_cache.get(cache_key)
    if cached is not None:
        ts, items = cached
        if now - ts < _CACHE_TTL:
            return items

    items = _scan_directory(real_path, virtual_prefix)
    _dir_cache[cache_key] = (now, items)
    return items


def invalidate_cache(real_path: Path) -> None:
    """Remove a directory from the listing cache and size cache."""
    key = str(real_path.resolve())
    _dir_cache.pop(key, None)
    # Also invalidate size caches (parent dirs may be affected)
    _size_cache.clear()


def get_dir_size(path: Path) -> int:
    """Get total size of all files in a directory tree (with TTL cache)."""
    if not path.exists():
        return 0

    cache_key = str(path.resolve())
    now = time.monotonic()
    cached = _size_cache.get(cache_key)
    if cached is not None:
        ts, size = cached
        if now - ts < _SIZE_CACHE_TTL:
            return size

    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size

    _size_cache[cache_key] = (now, total)
    return total


def delete_path(real_path: Path) -> None:
    """Delete a file or directory."""
    if real_path.is_dir():
        shutil.rmtree(real_path)
    elif real_path.is_file():
        real_path.unlink()


def rename_path(real_path: Path, new_name: str) -> Path:
    """Rename a file or directory. Returns new path."""
    if "/" in new_name or "\\" in new_name:
        raise PathSecurityError("Invalid name")
    new_path = real_path.parent / new_name
    if new_path.exists():
        raise FileExistsError(f"'{new_name}' already exists")
    real_path.rename(new_path)
    return new_path


def move_path(src: Path, dst_dir: Path, copy: bool = False) -> Path:
    """Move or copy a file/directory into dst_dir."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    target = dst_dir / src.name
    if target.exists():
        raise FileExistsError(f"'{src.name}' already exists in destination")

    if copy:
        if src.is_dir():
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)
    else:
        shutil.move(str(src), str(target))

    return target
