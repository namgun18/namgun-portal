from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str | None
    email: str | None
    avatar_url: str | None
    is_admin: bool
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class NativeCallbackRequest(BaseModel):
    code: str
    code_verifier: str
