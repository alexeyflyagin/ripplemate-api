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
from app.services.email_templates import render


class RateLimitError(Exception):
    """Raised when a verification email was requested too soon after the last one."""


CODE_LENGTH = 5
_CODE_UPPER_BOUND = 10**CODE_LENGTH


def _generate_code() -> str:
    return f"{secrets.randbelow(_CODE_UPPER_BOUND):0{CODE_LENGTH}d}"


def _hash_code(user_id, code: str) -> str:
    return hashlib.sha256(f"{user_id}:{code}".encode()).hexdigest()


def _password_reset_email(code: str, ttl_minutes: int) -> tuple[str, str, str]:
    subject = "Your password reset code"
    text = (
        "You requested a password reset.\n"
        f"Your code (valid {ttl_minutes} minutes): {code}\n"
        "If you did not request this, ignore this email."
    )
    html = render("password_reset.html", code=code, ttl=ttl_minutes)
    return subject, text, html


def _email_verify_email(code: str, ttl_minutes: int) -> tuple[str, str, str]:
    subject = "Your email confirmation code"
    text = (
        "Confirm your email address with the code below "
        f"(valid {ttl_minutes // 60} hours): {code}"
    )
    html = render("email_verify.html", code=code, ttl=ttl_minutes // 60)
    return subject, text, html


# One entry per confirmation type. Add a new VerificationAction plus a row here
# to introduce a new flow; the code/email machinery is reused unchanged.
# ttl is read lazily so an env override of the config value is always picked up.
_ACTION_CONFIG = {
    VerificationAction.PASSWORD_RESET: {
        "ttl": lambda: settings.password_reset_token_ttl_minutes,
        "build_email": _password_reset_email,
    },
    VerificationAction.EMAIL_VERIFY: {
        "ttl": lambda: settings.email_verify_token_ttl_minutes,
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

    async def _create_code(self, user_id, action: str, ttl_minutes: int) -> str:
        await self.repository.delete_expired()
        await self.repository.delete_for_user(user_id, action)

        code = _generate_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        await self.repository.create(
            user_id=user_id,
            token_hash=_hash_code(user_id, code),
            action=action,
            expires_at=expires_at,
        )
        return code

    async def _enforce_cooldown(self, user_id, action: str) -> None:
        # Note: only real users are rate-limited here (codes carry user_id).
        # A request for a non-existent email still returns neutrally, so the
        # 429-vs-200 difference is a minor, accepted trade-off for now.
        last = await self.repository.get_latest_for_user(user_id, action)
        if last is None:
            return
        created_at = last.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - created_at).total_seconds()
        if elapsed < settings.resend_cooldown_seconds:
            raise RateLimitError()

    async def _issue_and_send(self, user: User, action: str) -> None:
        config = _ACTION_CONFIG[action]
        ttl_minutes = config["ttl"]()

        await self._enforce_cooldown(user.id, action)

        code = await self._create_code(user.id, action, ttl_minutes)
        subject, text, html = config["build_email"](code, ttl_minutes)
        await self.email_sender.send(
            to=user.email, subject=subject, text=text, html=html
        )

    async def _consume_code(
        self, email: str, raw_code: str, action: str
    ) -> tuple[VerificationToken, User] | None:
        user = await self._get_user_by_email(email)
        if user is None:
            return None

        record = await self.repository.get_latest_for_user(user.id, action)
        if record is None:
            return None

        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            await self.repository.delete(record)
            return None

        if record.attempts >= settings.verification_code_max_attempts:
            await self.repository.delete(record)
            return None

        if not secrets.compare_digest(_hash_code(user.id, raw_code), record.token_hash):
            await self.repository.increment_attempts(record)
            return None

        return record, user

    async def request_password_reset(self, email: str) -> None:
        user = await self._get_user_by_email(email)
        if user is None or not user.is_active or not user.is_verified:
            return
        await self._issue_and_send(user, VerificationAction.PASSWORD_RESET)

    async def reset_password(self, email: str, raw_code: str, new_password: str) -> bool:
        result = await self._consume_code(email, raw_code, VerificationAction.PASSWORD_RESET)
        if result is None:
            return False
        record, user = result

        user.hashed_password = self.password_helper.hash(new_password)
        await self.repository.delete(record)
        await self.session.commit()
        return True

    async def request_email_verification(self, email: str) -> None:
        user = await self._get_user_by_email(email)
        if user is None or not user.is_active or user.is_verified:
            return
        await self._issue_and_send(user, VerificationAction.EMAIL_VERIFY)

    async def verify_email(self, email: str, raw_code: str) -> bool:
        result = await self._consume_code(email, raw_code, VerificationAction.EMAIL_VERIFY)
        if result is None:
            return False
        record, user = result

        user.is_verified = True
        await self.repository.delete(record)
        await self.session.commit()
        return True
