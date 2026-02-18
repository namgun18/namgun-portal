from datetime import datetime

from pydantic import BaseModel


class FileItem(BaseModel):
    name: str
    path: str  # virtual path (my/... or shared/...)
    is_dir: bool
    size: int = 0
    modified_at: datetime | None = None
    mime_type: str | None = None


class FileListResponse(BaseModel):
    path: str
    items: list[FileItem]


class StorageInfo(BaseModel):
    personal_used: int  # bytes
    shared_used: int
    total_available: int  # 0 = unlimited


class MkdirRequest(BaseModel):
    path: str


class RenameRequest(BaseModel):
    path: str
    new_name: str


class MoveRequest(BaseModel):
    src: str
    dst: str
    copy: bool = False


class ShareLinkCreate(BaseModel):
    path: str
    expires_in: str | None = None  # "1h", "1d", "7d", None=unlimited
    one_time: bool = False


class ShareLinkResponse(BaseModel):
    token: str
    url: str
    display_name: str
    expires_at: datetime | None
    max_downloads: int | None
    created_at: datetime


class ShareLinkListItem(BaseModel):
    id: str
    token: str
    display_name: str
    file_path: str
    expires_at: datetime | None
    max_downloads: int | None
    download_count: int
    created_at: datetime
