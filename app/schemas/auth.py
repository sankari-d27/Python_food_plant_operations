
from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
    role: str | None = None


class UserAuthResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
