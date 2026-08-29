import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification_token import VerificationToken


class VerificationTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        action: str,
        expires_at: datetime,
    ) -> VerificationToken:
        token = VerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            action=action,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str, action: str) -> VerificationToken | None:
        result = await self.session.execute(
            select(VerificationToken).where(
                VerificationToken.token_hash == token_hash,
                VerificationToken.action == action,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_for_user(
        self, user_id: uuid.UUID, action: str
    ) -> VerificationToken | None:
        result = await self.session.execute(
            select(VerificationToken)
            .where(
                VerificationToken.user_id == user_id,
                VerificationToken.action == action,
            )
            .order_by(VerificationToken.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def delete(self, token: VerificationToken) -> None:
        await self.session.delete(token)
        await self.session.commit()

    async def delete_expired(self) -> None:
        await self.session.execute(
            delete(VerificationToken).where(
                VerificationToken.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.session.commit()
