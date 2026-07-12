from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.account import Account
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository):
        self.repository = repository

    async def create_for_account(self, account: Account, payload: WorkspaceCreate):
        try:
            return await self.repository.create(account.id, payload.name)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Workspace with this name already exists",
            )

    async def rename_for_account(
        self, account: Account, workspace_id: int, payload: WorkspaceUpdate
    ):
        workspace = await self.repository.get_owned(workspace_id, account.id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        data = payload.model_dump(exclude_unset=True)
        if "name" not in data:
            return workspace

        try:
            return await self.repository.update_name(workspace, data["name"])
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Workspace with this name already exists",
            )

    async def delete_for_account(self, account: Account, workspace_id: int) -> None:
        workspace = await self.repository.get_owned(workspace_id, account.id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        await self.repository.delete(workspace)