from fastapi import APIRouter, Depends

from app.auth.deps import get_current_user
from app.db.models import User
from app.services.health import get_cached_status
from app.services.schemas import ServiceStatus

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("/status", response_model=list[ServiceStatus])
async def service_status(user: User = Depends(get_current_user)):
    """Return all service health statuses (authenticated)."""
    return get_cached_status()
