import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import app.models  # noqa: F401
from app.models.user import User
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_session
from main import app as fastapi_app


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(settings.test_database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_session():
        yield db_session

    fastapi_app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(client, db_session):
    await client.post(
        "/auth/register",
        json={
            "email": "settingsuser@example.com",
            "password": "password123",
            "display_name": "Settings User",
        },
    )

    result = await db_session.execute(
        select(User).where(User.email == "settingsuser@example.com")
    )
    user = result.scalar_one()
    user.is_verified = True
    await db_session.commit()

    response = await client.post(
        "/auth/jwt/login",
        data={"username": "settingsuser@example.com", "password": "password123"},
    )
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def workspace_id(authenticated_client):
    response = await authenticated_client.post("/workspaces", json={"name": "My Workspace"})
    return response.json()["id"]


@pytest_asyncio.fixture
async def category_id(authenticated_client, workspace_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/categories", json={"name": "My Category"}
    )
    return response.json()["id"]


@pytest_asyncio.fixture
async def card_id(authenticated_client, workspace_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "My Term"}
    )
    return response.json()["id"]


async def verify_user(db_session, email: str) -> None:
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_verified = True
    await db_session.commit()
