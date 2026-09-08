from fastapi import APIRouter, Depends, Query
from fastapi_users.exceptions import UserNotExists
from pydantic import EmailStr

from app.models import User
from app.models.account import Account
from app.schemas.account import AccountExists, AccountRead
from app.users import (
    UserManager,
    get_current_account,
    get_user_manager,
    current_active_user,
)

router = APIRouter()


@router.get("/exists", response_model=AccountExists)
async def check_account_exists(
        email: EmailStr = Query(...),
        user_manager: UserManager = Depends(get_user_manager),
):
    try:
        await user_manager.get_by_email(email)
        exists = True
    except UserNotExists:
        exists = False

    return AccountExists(exists=exists)


@router.get("", response_model=AccountRead)
async def get_my_account(
        user: User = Depends(current_active_user),
        account: Account = Depends(get_current_account),
):
    account_dict = account.__dict__.copy()
    account_dict["email"] = user.email
    account_dict["is_verified"] = user.is_verified

    return AccountRead.model_validate(account_dict)
