from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.verification_token import VerificationTokenRepository
from app.schemas.verification import (
    ErrorResponse,
    ResetPasswordRequest,
    MessageResponse,
    VerifyEmailRequest,
    ResetPassword,
    VerifyEmail,
)
from app.services.email import EmailSender, get_email_sender
from app.services.verification import RateLimitError, VerificationService
from app.users import UserManager, get_user_manager

router = APIRouter()

_NEUTRAL = MessageResponse(
    message="If an account matches, we've sent an email with a code."
)

_TOO_MANY_REQUESTS_RESPONSE = {
    status.HTTP_429_TOO_MANY_REQUESTS: {
        "model": ErrorResponse,
        "description": "A code was already requested recently; wait for the resend cooldown to elapse.",
        "content": {
            "application/json": {
                "example": {"detail": "Too many requests. Please wait before trying again."}
            }
        },
    },
}

_INVALID_CODE_RESPONSE = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": "The code is wrong, expired, already used, or the attempt limit was exceeded.",
        "content": {
            "application/json": {"example": {"detail": "Invalid or expired code"}}
        },
    },
}


def get_verification_service(
    session: AsyncSession = Depends(get_session),
    user_manager: UserManager = Depends(get_user_manager),
    email_sender: EmailSender = Depends(get_email_sender),
) -> VerificationService:
    return VerificationService(
        session=session,
        repository=VerificationTokenRepository(session),
        email_sender=email_sender,
        password_helper=user_manager.password_helper,
    )


@router.post(
    "/request-reset-password",
    response_model=MessageResponse,
    responses=_TOO_MANY_REQUESTS_RESPONSE,
)
async def forgot_password(
    payload: ResetPasswordRequest,
    service: VerificationService = Depends(get_verification_service),
):
    try:
        await service.request_password_reset(payload.email)
    except RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait before trying again.",
        )
    return _NEUTRAL


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    responses=_INVALID_CODE_RESPONSE,
)
async def reset_password(
    payload: ResetPassword,
    service: VerificationService = Depends(get_verification_service),
):
    ok = await service.reset_password(payload.email, payload.code, payload.password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code",
        )
    return MessageResponse(message="Password has been reset.")


@router.post(
    "/request-verify-email",
    response_model=MessageResponse,
    responses=_TOO_MANY_REQUESTS_RESPONSE,
)
async def request_verify_token(
    payload: VerifyEmailRequest,
    service: VerificationService = Depends(get_verification_service),
):
    try:
        await service.request_email_verification(payload.email)
    except RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait before trying again.",
        )
    return _NEUTRAL


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    responses=_INVALID_CODE_RESPONSE,
)
async def verify_email(
    payload: VerifyEmail,
    service: VerificationService = Depends(get_verification_service),
):
    ok = await service.verify_email(payload.email, payload.code)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code",
        )
    return MessageResponse(message="Email verified.")
