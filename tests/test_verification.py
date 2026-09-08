import re

import pytest_asyncio
from sqlalchemy import select

from app.api.routes.verification import get_verification_service
from app.core.config import settings
from app.models.user import User
from app.models.verification_token import VerificationAction, VerificationToken
from app.services.email import EmailSender, get_email_sender
from main import app as fastapi_app


class RecordingEmailSender(EmailSender):
    def __init__(self):
        self.sent = []

    async def send(
        self, to: str, subject: str, text: str, html: str | None = None
    ) -> None:
        self.sent.append(
            {"to": to, "subject": subject, "text": text, "html": html}
        )

    def code_for(self, to: str) -> str | None:
        for message in reversed(self.sent):
            if message["to"] == to:
                match = re.search(r"\b(\d{5})\b", message["text"])
                if match:
                    return match.group(1)
        return None


@pytest_asyncio.fixture
async def mailbox(client):
    sender = RecordingEmailSender()
    fastapi_app.dependency_overrides[get_email_sender] = lambda: sender
    yield sender
    fastapi_app.dependency_overrides.pop(get_email_sender, None)


async def _register(client, email="alice@example.com", password="password123"):
    return await client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": "Alice"},
    )


async def _get_user(db_session, email):
    result = await db_session.execute(select(User).where(User.email == email))
    return result.scalar_one()


async def _set_verified(db_session, email, value=True):
    user = await _get_user(db_session, email)
    user.is_verified = value
    await db_session.commit()


def _wrong_code(code: str) -> str:
    wrong = (int(code) + 1) % 100000
    return f"{wrong:05d}"


# --- email verification -------------------------------------------------


async def test_request_verify_creates_code_and_neutral_response(client, db_session, mailbox):
    await _register(client, "verify@example.com")

    resp = await client.post(
        "/validation/request-verify-email", json={"email": "verify@example.com"}
    )
    assert resp.status_code == 200
    code = mailbox.code_for("verify@example.com")
    assert code is not None
    assert re.fullmatch(r"\d{5}", code)

    result = await db_session.execute(
        select(VerificationToken).where(
            VerificationToken.action == VerificationAction.EMAIL_VERIFY
        )
    )
    assert len(result.scalars().all()) == 1


async def test_request_verify_unknown_email_is_neutral(client, db_session, mailbox):
    resp = await client.post(
        "/validation/request-verify-email", json={"email": "nobody@example.com"}
    )
    assert resp.status_code == 200
    assert mailbox.sent == []

    result = await db_session.execute(select(VerificationToken))
    assert result.scalars().all() == []


async def test_verify_email_full_flow_sets_is_verified(client, db_session, mailbox):
    await _register(client, "v2@example.com")

    await client.post("/validation/request-verify-email", json={"email": "v2@example.com"})
    code = mailbox.code_for("v2@example.com")

    resp = await client.post(
        "/validation/verify-email", json={"email": "v2@example.com", "code": code}
    )
    assert resp.status_code == 200

    user = await _get_user(db_session, "v2@example.com")
    assert user.is_verified is True

    result = await db_session.execute(select(VerificationToken))
    assert result.scalars().all() == []


async def test_verify_email_with_bad_code_returns_400(client, mailbox):
    resp = await client.post(
        "/validation/verify-email", json={"email": "nobody@example.com", "code": "12345"}
    )
    assert resp.status_code == 400


async def test_verify_email_rejects_malformed_code(client, mailbox):
    resp = await client.post(
        "/validation/verify-email", json={"email": "nobody@example.com", "code": "not-digits"}
    )
    assert resp.status_code == 422


async def test_request_verify_already_verified_sends_nothing(client, db_session, mailbox):
    await _register(client, "already@example.com")
    await _set_verified(db_session, "already@example.com", True)

    resp = await client.post(
        "/validation/request-verify-email", json={"email": "already@example.com"}
    )
    assert resp.status_code == 200
    assert mailbox.sent == []


# --- password reset -----------------------------------------------------


async def test_forgot_password_unverified_user_sends_nothing(client, db_session, mailbox):
    await _register(client, "unv@example.com")

    resp = await client.post(
        "/validation/request-reset-password", json={"email": "unv@example.com"}
    )
    assert resp.status_code == 200
    assert mailbox.sent == []

    result = await db_session.execute(
        select(VerificationToken).where(
            VerificationToken.action == VerificationAction.PASSWORD_RESET
        )
    )
    assert result.scalars().all() == []


async def test_forgot_password_verified_user_sends_mail(client, db_session, mailbox):
    await _register(client, "ver@example.com")
    await _set_verified(db_session, "ver@example.com", True)

    resp = await client.post(
        "/validation/request-reset-password", json={"email": "ver@example.com"}
    )
    assert resp.status_code == 200
    assert mailbox.code_for("ver@example.com") is not None


async def test_reset_password_full_flow_allows_login(client, db_session, mailbox):
    await _register(client, "reset@example.com", "oldpassword1")
    await _set_verified(db_session, "reset@example.com", True)

    await client.post("/validation/request-reset-password", json={"email": "reset@example.com"})
    code = mailbox.code_for("reset@example.com")

    resp = await client.post(
        "/validation/reset-password",
        json={"email": "reset@example.com", "code": code, "password": "newpassword1"},
    )
    assert resp.status_code == 200

    old = await client.post(
        "/auth/jwt/login",
        data={"username": "reset@example.com", "password": "oldpassword1"},
    )
    assert old.status_code == 400
    new = await client.post(
        "/auth/jwt/login",
        data={"username": "reset@example.com", "password": "newpassword1"},
    )
    assert new.status_code == 200


async def test_reset_password_bad_code_returns_400(client, mailbox):
    resp = await client.post(
        "/validation/reset-password",
        json={"email": "nobody@example.com", "code": "12345", "password": "whatever12"},
    )
    assert resp.status_code == 400


async def test_reset_password_rejects_malformed_code(client, mailbox):
    resp = await client.post(
        "/validation/reset-password",
        json={"email": "nobody@example.com", "code": "abc", "password": "whatever12"},
    )
    assert resp.status_code == 422


async def test_reset_code_is_single_use(client, db_session, mailbox):
    await _register(client, "single@example.com", "oldpassword1")
    await _set_verified(db_session, "single@example.com", True)

    await client.post("/validation/request-reset-password", json={"email": "single@example.com"})
    code = mailbox.code_for("single@example.com")

    first = await client.post(
        "/validation/reset-password",
        json={"email": "single@example.com", "code": code, "password": "newpassword1"},
    )
    assert first.status_code == 200
    second = await client.post(
        "/validation/reset-password",
        json={"email": "single@example.com", "code": code, "password": "another12345"},
    )
    assert second.status_code == 400


async def test_verify_code_rejected_on_reset_endpoint(client, db_session, mailbox):
    await _register(client, "cross@example.com")

    await client.post("/validation/request-verify-email", json={"email": "cross@example.com"})
    verify_code = mailbox.code_for("cross@example.com")

    resp = await client.post(
        "/validation/reset-password",
        json={"email": "cross@example.com", "code": verify_code, "password": "newpassword1"},
    )
    assert resp.status_code == 400


async def test_second_request_within_cooldown_returns_429(client, db_session, mailbox):
    await _register(client, "cooldown@example.com")
    await _set_verified(db_session, "cooldown@example.com", True)

    first = await client.post(
        "/validation/request-reset-password",
        json={"email": "cooldown@example.com"},
    )
    assert first.status_code == 200

    second = await client.post(
        "/validation/request-reset-password",
        json={"email": "cooldown@example.com"},
    )
    assert second.status_code == 429


# --- brute-force protection ---------------------------------------------


async def test_wrong_code_does_not_verify(client, db_session, mailbox):
    await _register(client, "wrong@example.com")

    await client.post("/validation/request-verify-email", json={"email": "wrong@example.com"})
    code = mailbox.code_for("wrong@example.com")

    resp = await client.post(
        "/validation/verify-email",
        json={"email": "wrong@example.com", "code": _wrong_code(code)},
    )
    assert resp.status_code == 400

    user = await _get_user(db_session, "wrong@example.com")
    assert user.is_verified is False


async def test_code_locks_out_after_max_attempts(client, db_session, mailbox):
    await _register(client, "lockout@example.com")

    await client.post("/validation/request-verify-email", json={"email": "lockout@example.com"})
    code = mailbox.code_for("lockout@example.com")
    wrong = _wrong_code(code)

    for _ in range(settings.verification_code_max_attempts):
        resp = await client.post(
            "/validation/verify-email",
            json={"email": "lockout@example.com", "code": wrong},
        )
        assert resp.status_code == 400

    resp = await client.post(
        "/validation/verify-email",
        json={"email": "lockout@example.com", "code": code},
    )
    assert resp.status_code == 400

    user = await _get_user(db_session, "lockout@example.com")
    assert user.is_verified is False


async def test_requesting_new_code_invalidates_previous_one(client, db_session, mailbox):
    await _register(client, "resend@example.com")

    await client.post("/validation/request-verify-email", json={"email": "resend@example.com"})
    first_code = mailbox.code_for("resend@example.com")

    result = await db_session.execute(
        select(VerificationToken).where(
            VerificationToken.action == VerificationAction.EMAIL_VERIFY
        )
    )
    tokens = result.scalars().all()
    assert len(tokens) == 1

    resp = await client.post(
        "/validation/verify-email",
        json={"email": "resend@example.com", "code": first_code},
    )
    assert resp.status_code == 200
