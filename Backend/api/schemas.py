from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(
        min_length=6,
        max_length=6
    )


class ResendOTPRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(
        min_length=8,
        max_length=128
    )


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=128
    )
    new_password: str = Field(
        min_length=8,
        max_length=128
    )


class MessageResponse(BaseModel):
    message: str





class CreateSessionRequest(BaseModel):
    title: str = Field(
        default="New Chat",
        min_length=1,
        max_length=200
    )

    ticker: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=20
    )


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200
    )

    ticker: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=20
    )


class SessionResponse(BaseModel):
    id: str
    title: str
    ticker: Optional[str] = None
    is_deleted: bool


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    page: int
    page_size: int


class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        max_length=100
    )

    message: str = Field(
        min_length=1,
        max_length=10000
    )


class ChatResponse(BaseModel):
    session_id: str

    intent: str

    response: Optional[str] = None

    recommendation_candidates: Optional[list] = None