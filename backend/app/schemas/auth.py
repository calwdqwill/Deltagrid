from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    username: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: Optional[str] = None
    username: Optional[str] = None
    plan: str = "free"
    feature_flags: Optional[dict[str, str]] = None


class AuthResponse(Token):
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class TelegramAuthRequest(BaseModel):
    id: int
    first_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: Optional[int] = None
    hash: Optional[str] = None


class Web3ChallengeRequest(BaseModel):
    wallet_address: str


class Web3VerifyRequest(BaseModel):
    wallet_address: str
    signature: str
    nonce: str
