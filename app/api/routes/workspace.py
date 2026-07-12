from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.account import Account
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate
from app.services.workspace import WorkspaceService
from app.users import get_current_account

router = APIRouter()


def get_workspace_service(session: AsyncSession = Depends(get_session)) -> WorkspaceService:
    return WorkspaceService(WorkspaceRepository(session))


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    account: Account = Depends(get_current_account),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return await service.create_for_account(account, payload)


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
async def rename_workspace(
    workspace_id: int,
    payload: WorkspaceUpdate,
    account: Account = Depends(get_current_account),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return await service.rename_for_account(account, workspace_id, payload)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    account: Account = Depends(get_current_account),
    service: WorkspaceService = Depends(get_workspace_service),
):
    await service.delete_for_account(account, workspace_id)