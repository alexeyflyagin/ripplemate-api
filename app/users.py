import uuid

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, InvalidPasswordException, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Settings, Account, Workspace
from app.core.config import settings
from app.db.session import get_session
from app.models import Settings, Account
from app.models.user import User


async def get_user_db(session: AsyncSession = Depends(get_session)):
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def validate_password(self, password: str, user) -> None:
        if len(password) < 6:
            raise InvalidPasswordException(reason="Password must be at least 6 characters long")

    async def create(self, user_create, safe: bool = False, request=None) -> User:
        user = await super().create(user_create, safe=safe, request=request)

        session = self.user_db.session

        new_settings = Settings()
        session.add(new_settings)
        await session.flush()

        account = Account(
            user_id=user.id,
            settings_id=new_settings.id,
            display_name=user_create.display_name,
        )
        session.add(account)
        await session.flush()

        workspace = Workspace(owner_id=account.id, name="My workspace")
        session.add(workspace)
        await session.commit()

        return user


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.secret_key, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)


async def get_current_account(
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_session),
) -> Account:
    result = await session.execute(select(Account).where(Account.user_id == user.id))
    return result.scalar_one()
