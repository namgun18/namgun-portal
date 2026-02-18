from pydantic import BaseModel


class ServiceStatus(BaseModel):
    name: str
    url: str | None  # external URL (None for internal_only display)
    status: str  # "ok" | "down" | "checking"
    response_ms: int | None
    internal_only: bool
