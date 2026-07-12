from fastapi import APIRouter, Depends

from app.models.account import Account
from app.schemas.account import AccountRead
from app.users import get_current_account

router = APIRouter()


@router.get("", response_model=AccountRead)
async def get_my_account(account: Account = Depends(get_current_account)):
    return AccountRead.model_validate(account)
