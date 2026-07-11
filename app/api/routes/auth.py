from fastapi import APIRouter

from app.schemas.user import UserCreate, UserRead
from app.users import auth_backend, fastapi_users

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["auth"],
)