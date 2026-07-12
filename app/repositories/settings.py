from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import Settings


class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, settings_id: int) -> Settings:
        result = await self.session.execute(
            select(Settings).where(Settings.id == settings_id)
        )
        return result.scalar_one()

    async def update(self, settings: Settings, data: dict) -> Settings:
        for field, value in data.items():
            setattr(settings, field, value)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings