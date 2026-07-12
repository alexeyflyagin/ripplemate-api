from app.models.account import Account
from app.repositories.settings import SettingsRepository
from app.schemas.settings import SettingsUpdate


class SettingsService:
    def __init__(self, repository: SettingsRepository):
        self.repository = repository

    async def get_for_account(self, account: Account):
        return await self.repository.get_by_id(account.settings_id)

    async def update_for_account(self, account: Account, payload: SettingsUpdate):
        settings = await self.repository.get_by_id(account.settings_id)
        data = payload.model_dump(exclude_unset=True)
        return await self.repository.update(settings, data)