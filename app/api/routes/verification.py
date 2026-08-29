from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.verification_token import VerificationTokenRepository
from app.schemas.verification import (
    ResetPasswordRequest,
    MessageResponse,
    VerifyEmailRequest,
    ResetPassword,
    VerifyEmail,
)
from app.services.email import EmailSender, get_email_sender
from app.services.verification import VerificationService
from app.users import UserManager, get_user_manager

router = APIRouter()

_NEUTRAL = MessageResponse(
    message="If an account matches, we've sent an email with further instructions."
)


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


@router.post("/request-reset-password", response_model=MessageResponse)
async def forgot_password(
    payload: ResetPasswordRequest,
    service: VerificationService = Depends(get_verification_service),
):
    await service.request_password_reset(payload.email)
    return _NEUTRAL


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPassword,
    service: VerificationService = Depends(get_verification_service),
):
    ok = await service.reset_password(payload.token, payload.password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )
    return MessageResponse(message="Password has been reset.")


@router.post("/request-verify-email", response_model=MessageResponse)
async def request_verify_token(
    payload: VerifyEmailRequest,
    service: VerificationService = Depends(get_verification_service),
):
    await service.request_email_verification(payload.email)
    return _NEUTRAL


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmail,
    service: VerificationService = Depends(get_verification_service),
):
    ok = await service.verify_email(payload.token)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )
    return MessageResponse(message="Email verified.")
