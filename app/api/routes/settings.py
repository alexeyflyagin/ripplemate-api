from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.account import Account
from app.repositories.settings import SettingsRepository
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.services.settings import SettingsService
from app.users import get_current_account

router = APIRouter()


def get_settings_service(session: AsyncSession = Depends(get_session)) -> SettingsService:
    return SettingsService(SettingsRepository(session))


@router.get("", response_model=SettingsRead)
async def get_settings(
    account: Account = Depends(get_current_account),
    service: SettingsService = Depends(get_settings_service),
):
    return await service.get_for_account(account)


@router.patch("", response_model=SettingsRead)
async def update_settings(
    payload: SettingsUpdate,
    account: Account = Depends(get_current_account),
    service: SettingsService = Depends(get_settings_service),
):
    return await service.update_for_account(account, payload)