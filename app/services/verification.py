import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.verification_token import VerificationAction, VerificationToken
from app.repositories.verification_token import VerificationTokenRepository
from app.services.email import EmailSender


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _password_reset_email(link: str, ttl_minutes: int) -> tuple[str, str]:
    subject = "Password reset"
    body = (
        "You requested a password reset.\n"
        f"Open this link to set a new password (valid {ttl_minutes} minutes):\n{link}\n"
        "If you did not request this, ignore this email."
    )
    return subject, body


def _email_verify_email(link: str, ttl_minutes: int) -> tuple[str, str]:
    subject = "Confirm your email"
    body = (
        "Confirm your email address by opening this link "
        f"(valid {ttl_minutes // 60} hours):\n{link}"
    )
    return subject, body


# One entry per confirmation type. Add a new VerificationAction plus a row here
# to introduce a new flow; the token/email machinery is reused unchanged.
# ttl is read lazily so an env override of the config value is always picked up.
_ACTION_CONFIG = {
    VerificationAction.PASSWORD_RESET: {
        "ttl": lambda: settings.password_reset_token_ttl_minutes,
        "path": "/reset-password",
        "build_email": _password_reset_email,
    },
    VerificationAction.EMAIL_VERIFY: {
        "ttl": lambda: settings.email_verify_token_ttl_minutes,
        "path": "/verify-email",
        "build_email": _email_verify_email,
    },
}


class VerificationService:
    def __init__(
        self,
        session: AsyncSession,
        repository: VerificationTokenRepository,
        email_sender: EmailSender,
        password_helper,
    ):
        self.session = session
        self.repository = repository
        self.email_sender = email_sender
        self.password_helper = password_helper

    async def _get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def _create_token(self, user_id, action: str, ttl_minutes: int) -> str:
        await self.repository.delete_expired()

        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        await self.repository.create(
            user_id=user_id,
            token_hash=_hash_token(raw_token),
            action=action,
            expires_at=expires_at,
        )
        return raw_token

    async def _issue_and_send(self, user: User, action: str) -> None:
        config = _ACTION_CONFIG[action]
        ttl_minutes = config["ttl"]()

        raw_token = await self._create_token(user.id, action, ttl_minutes)
        link = f"{settings.frontend_url}{config['path']}?token={raw_token}"
        subject, body = config["build_email"](link, ttl_minutes)
        await self.email_sender.send(to=user.email, subject=subject, body=body)

    async def _consume_token(self, raw_token: str, action: str) -> VerificationToken | None:
        record = await self.repository.get_by_hash(_hash_token(raw_token), action)
        if record is None:
            return None
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            await self.repository.delete(record)
            return None
        return record

    async def request_password_reset(self, email: str) -> None:
        user = await self._get_user_by_email(email)
        if user is None or not user.is_active or not user.is_verified:
            return
        await self._issue_and_send(user, VerificationAction.PASSWORD_RESET)

    async def reset_password(self, raw_token: str, new_password: str) -> bool:
        record = await self._consume_token(raw_token, VerificationAction.PASSWORD_RESET)
        if record is None:
            return False

        user = await self.session.get(User, record.user_id)
        if user is None:
            await self.repository.delete(record)
            return False

        user.hashed_password = self.password_helper.hash(new_password)
        await self.repository.delete(record)
        await self.session.commit()
        return True

    async def request_email_verification(self, email: str) -> None:
        user = await self._get_user_by_email(email)
        if user is None or not user.is_active or user.is_verified:
            return
        await self._issue_and_send(user, VerificationAction.EMAIL_VERIFY)

    async def verify_email(self, raw_token: str) -> bool:
        record = await self._consume_token(raw_token, VerificationAction.EMAIL_VERIFY)
        if record is None:
            return False

        user = await self.session.get(User, record.user_id)
        if user is None:
            await self.repository.delete(record)
            return False

        user.is_verified = True
        await self.repository.delete(record)
        await self.session.commit()
        return True
