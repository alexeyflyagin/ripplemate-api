import pytest
from sqlalchemy import select

from app.models import Workspace
from app.models.account import Account
from app.models.settings import Settings
from app.models.user import User


async def test_register_creates_user_account_settings_and_workspace(client, db_session):
    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "display_name": "New User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "display_name" not in data

    result = await db_session.execute(
        select(Account).where(Account.user_id == data["id"])
    )
    account = result.scalar_one()
    assert account.display_name == "New User"

    result = await db_session.execute(
        select(Settings).where(Settings.id == account.settings_id)
    )
    settings_row = result.scalar_one()
    assert settings_row.font == "sans-serif"
    assert settings_row.language == "auto"
    assert settings_row.theme == "auto"

    result = await db_session.execute(
        select(Workspace).where(Workspace.owner_id == account.id)
    )
    workspace = result.scalar_one()
    assert workspace.name == "My workspace"


async def test_register_rejects_short_password(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "shortpass@example.com",
            "password": "123",
            "display_name": "Someone",
        },
    )

    assert response.status_code == 400


async def test_register_rejects_blank_display_name(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "blankname@example.com",
            "password": "password123",
            "display_name": "   ",
        },
    )

    assert response.status_code == 422


async def test_register_rejects_display_name_too_long(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "longname@example.com",
            "password": "password123",
            "display_name": "x" * 33,
        },
    )

    assert response.status_code == 422


async def test_register_rejects_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "display_name": "First User",
    }

    first_response = await client.post("/auth/register", json=payload)
    assert first_response.status_code == 201

    second_response = await client.post(
        "/auth/register", json={**payload, "display_name": "Second User"}
    )
    assert second_response.status_code == 400


async def test_register_ignores_is_superuser_flag(client, db_session):
    response = await client.post(
        "/auth/register",
        json={
            "email": "wannabe@example.com",
            "password": "password123",
            "display_name": "Wannabe Admin",
            "is_superuser": True,
        },
    )
    assert response.status_code == 201

    result = await db_session.execute(
        select(User).where(User.email == "wannabe@example.com")
    )
    user = result.scalar_one()
    assert user.is_superuser is False


async def test_login_with_registered_user(client):
    await client.post(
        "/auth/register",
        json={
            "email": "logintest@example.com",
            "password": "password123",
            "display_name": "Login Test",
        },
    )

    response = await client.post(
        "/auth/jwt/login",
        data={"username": "logintest@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_rejects_wrong_password(client):
    await client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "password123",
            "display_name": "Someone",
        },
    )

    response = await client.post(
        "/auth/jwt/login",
        data={"username": "wrongpass@example.com", "password": "notthepassword"},
    )

    assert response.status_code == 400


async def test_login_rejects_unknown_email(client):
    response = await client.post(
        "/auth/jwt/login",
        data={"username": "doesnotexist@example.com", "password": "password123"},
    )

    assert response.status_code == 400


async def test_register_rejects_malformed_email(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
            "display_name": "Someone",
        },
    )

    assert response.status_code == 422


async def test_register_treats_email_domain_case_sensitively(client):
    await client.post(
        "/auth/register",
        json={
            "email": "casetest@Example.com",
            "password": "password123",
            "display_name": "First",
        },
    )

    response = await client.post(
        "/auth/register",
        json={
            "email": "casetest@example.com",
            "password": "password123",
            "display_name": "Second",
        },
    )

    assert response.status_code == 400


async def test_register_treats_email_case_insensitively(client):
    await client.post(
        "/auth/register",
        json={
            "email": "CaseTest@example.com",
            "password": "password123",
            "display_name": "First",
        },
    )

    response = await client.post(
        "/auth/register",
        json={
            "email": "casetest@example.com",
            "password": "password123",
            "display_name": "Second",
        },
    )

    assert response.status_code == 400


async def test_register_deletes_orphaned_user_if_account_creation_fails(
    client, db_session, monkeypatch
):
    import app.users as users_module
    from app.models.user import User

    class ExplodingWorkspace:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Simulated failure")

    monkeypatch.setattr(users_module, "Workspace", ExplodingWorkspace)

    with pytest.raises(RuntimeError, match="Simulated failure"):
        await client.post(
            "/auth/register",
            json={
                "email": "shouldnotexist@example.com",
                "password": "password123",
                "display_name": "Ghost User",
            },
        )

    result = await db_session.execute(
        select(User).where(User.email == "shouldnotexist@example.com")
    )
    assert result.scalar_one_or_none() is None
