import re

import pytest_asyncio
from sqlalchemy import select

from app.api.routes.verification import get_verification_service
from app.models.user import User
from app.models.verification_token import VerificationAction, VerificationToken
from app.services.email import EmailSender, get_email_sender
from main import app as fastapi_app


class RecordingEmailSender(EmailSender):
    def __init__(self):
        self.sent = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})

    def token_for(self, to: str) -> str | None:
        for message in reversed(self.sent):
            if message["to"] == to:
                match = re.search(r"token=([\w\-]+)", message["body"])
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


# --- email verification -------------------------------------------------


async def test_request_verify_creates_token_and_neutral_response(client, db_session, mailbox):
    await _register(client, "verify@example.com")

    resp = await client.post(
        "/auth/request-verify-token", json={"email": "verify@example.com"}
    )
    assert resp.status_code == 200
    assert mailbox.token_for("verify@example.com") is not None

    result = await db_session.execute(
        select(VerificationToken).where(
            VerificationToken.action == VerificationAction.EMAIL_VERIFY
        )
    )
    assert len(result.scalars().all()) == 1


async def test_request_verify_unknown_email_is_neutral(client, db_session, mailbox):
    resp = await client.post(
        "/auth/request-verify-token", json={"email": "nobody@example.com"}
    )
    assert resp.status_code == 200
    assert mailbox.sent == []

    result = await db_session.execute(select(VerificationToken))
    assert result.scalars().all() == []


async def test_verify_email_full_flow_sets_is_verified(client, db_session, mailbox):
    await _register(client, "v2@example.com")

    await client.post("/auth/request-verify-token", json={"email": "v2@example.com"})
    token = mailbox.token_for("v2@example.com")

    resp = await client.post("/auth/verify", json={"token": token})
    assert resp.status_code == 200

    user = await _get_user(db_session, "v2@example.com")
    assert user.is_verified is True

    result = await db_session.execute(select(VerificationToken))
    assert result.scalars().all() == []


async def test_verify_email_with_bad_token_returns_400(client, mailbox):
    resp = await client.post("/auth/verify", json={"token": "not-a-real-token"})
    assert resp.status_code == 400


async def test_request_verify_already_verified_sends_nothing(client, db_session, mailbox):
    await _register(client, "already@example.com")
    await _set_verified(db_session, "already@example.com", True)

    resp = await client.post(
        "/auth/request-verify-token", json={"email": "already@example.com"}
    )
    assert resp.status_code == 200
    assert mailbox.sent == []


# --- password reset -----------------------------------------------------


async def test_forgot_password_unverified_user_sends_nothing(client, db_session, mailbox):
    await _register(client, "unv@example.com")

    resp = await client.post(
        "/auth/forgot-password", json={"email": "unv@example.com"}
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
        "/auth/forgot-password", json={"email": "ver@example.com"}
    )
    assert resp.status_code == 200
    assert mailbox.token_for("ver@example.com") is not None


async def test_reset_password_full_flow_allows_login(client, db_session, mailbox):
    await _register(client, "reset@example.com", "oldpassword1")
    await _set_verified(db_session, "reset@example.com", True)

    await client.post("/auth/forgot-password", json={"email": "reset@example.com"})
    token = mailbox.token_for("reset@example.com")

    resp = await client.post(
        "/auth/reset-password", json={"token": token, "password": "newpassword1"}
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


async def test_reset_password_bad_token_returns_400(client, mailbox):
    resp = await client.post(
        "/auth/reset-password", json={"token": "bogus", "password": "whatever12"}
    )
    assert resp.status_code == 400


async def test_reset_token_is_single_use(client, db_session, mailbox):
    await _register(client, "single@example.com", "oldpassword1")
    await _set_verified(db_session, "single@example.com", True)

    await client.post("/auth/forgot-password", json={"email": "single@example.com"})
    token = mailbox.token_for("single@example.com")

    first = await client.post(
        "/auth/reset-password", json={"token": token, "password": "newpassword1"}
    )
    assert first.status_code == 200
    second = await client.post(
        "/auth/reset-password", json={"token": token, "password": "another12345"}
    )
    assert second.status_code == 400


async def test_verify_token_rejected_on_reset_endpoint(client, db_session, mailbox):
    await _register(client, "cross@example.com")

    await client.post("/auth/request-verify-token", json={"email": "cross@example.com"})
    verify_token = mailbox.token_for("cross@example.com")

    resp = await client.post(
        "/auth/reset-password", json={"token": verify_token, "password": "newpassword1"}
    )
    assert resp.status_code == 400
