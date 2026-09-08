from pydantic import BaseModel, EmailStr, Field

CODE_PATTERN = r"^\d{5}$"


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    email: EmailStr
    code: str = Field(pattern=CODE_PATTERN)
    password: str = Field(min_length=8)


class VerifyEmailRequest(BaseModel):
    email: EmailStr


class VerifyEmail(BaseModel):
    email: EmailStr
    code: str = Field(pattern=CODE_PATTERN)


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
