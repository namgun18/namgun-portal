"""Dashboard API router — read-only game server status via Docker socket."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.deps import get_current_user
from app.db.models import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class GameServer(BaseModel):
    name: str
    status: str  # "running" | "exited" | ...
    game: str = ""


@router.get("/game-servers", response_model=list[GameServer])
async def list_game_servers(user: User = Depends(get_current_user)):
    """List game-panel managed containers (read-only Docker socket query)."""
    try:
        import docker

        client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
        containers = client.containers.list(
            all=True, filters={"label": "game-panel.managed=true"}
        )
        result = []
        for c in containers:
            labels = c.labels or {}
            result.append(
                GameServer(
                    name=labels.get("game-panel.description", c.name),
                    status=c.status,
                    game=labels.get("game-panel.game", ""),
                )
            )
        client.close()
        return result
    except Exception:
        return []
