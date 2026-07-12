from app.models.account import Account
from app.repositories.settings import SettingsRepository
from app.schemas.settings import SettingsRead, SettingsUpdate


class SettingsService:
    def __init__(self, repository: SettingsRepository):
        self.repository = repository

    async def get_for_account(self, account: Account) -> SettingsRead:
        settings = await self.repository.get_by_id(account.settings_id)
        return SettingsRead.model_validate(settings)

    async def update_for_account(self, account: Account, payload: SettingsUpdate) -> SettingsRead:
        settings = await self.repository.get_by_id(account.settings_id)
        data = payload.model_dump(exclude_unset=True)
        settings = await self.repository.update(settings, data)
        return SettingsRead.model_validate(settings)