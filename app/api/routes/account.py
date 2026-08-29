from fastapi import APIRouter, Depends

from app.models import User
from app.models.account import Account
from app.schemas.account import AccountRead
from app.users import get_current_account, current_active_user

router = APIRouter()


@router.get("", response_model=AccountRead)
async def get_my_account(
        user: User = Depends(current_active_user),
        account: Account = Depends(get_current_account),
):
    account_dict = account.__dict__.copy()
    account_dict["email"] = user.email
    account_dict["is_verified"] = user.is_verified

    return AccountRead.model_validate(account_dict)
