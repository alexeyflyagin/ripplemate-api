from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.account import Account
from app.repositories.category import CategoryRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category import CategoryService
from app.users import get_verified_account

router = APIRouter()


def get_category_service(session: AsyncSession = Depends(get_session)) -> CategoryService:
    return CategoryService(CategoryRepository(session), WorkspaceRepository(session))


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    workspace_id: str,
    payload: CategoryCreate,
    account: Account = Depends(get_verified_account),
    service: CategoryService = Depends(get_category_service),
):
    return await service.create_in_workspace(account, workspace_id, payload)


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    workspace_id: str,
    account: Account = Depends(get_verified_account),
    service: CategoryService = Depends(get_category_service),
):
    return await service.list_in_workspace(account, workspace_id)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    workspace_id: str,
    category_id: str,
    account: Account = Depends(get_verified_account),
    service: CategoryService = Depends(get_category_service),
):
    return await service.get_in_workspace(account, workspace_id, category_id)


@router.patch("/{category_id}", response_model=CategoryRead)
async def rename_category(
    workspace_id: str,
    category_id: str,
    payload: CategoryUpdate,
    account: Account = Depends(get_verified_account),
    service: CategoryService = Depends(get_category_service),
):
    return await service.rename_in_workspace(account, workspace_id, category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    workspace_id: str,
    category_id: str,
    account: Account = Depends(get_verified_account),
    service: CategoryService = Depends(get_category_service),
):
    await service.delete_in_workspace(account, workspace_id, category_id)