from pydantic import BaseModel, EmailStr, Field


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str
    password: str = Field(min_length=8)


class VerifyEmailRequest(BaseModel):
    email: EmailStr


class VerifyEmail(BaseModel):
    token: str


class MessageResponse(BaseModel):
    message: str
