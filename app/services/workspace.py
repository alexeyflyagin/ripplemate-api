from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.account import Account
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository):
        self.repository = repository

    async def create_for_account(self, account: Account, payload: WorkspaceCreate) -> WorkspaceRead:
        try:
            workspace = await self.repository.create(account.id, payload.name)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Workspace with this name already exists",
            )
        return WorkspaceRead.model_validate(workspace)

    async def list_for_account(self, account: Account) -> list[WorkspaceRead]:
        workspaces = await self.repository.list_owned(account.id)
        return [WorkspaceRead.model_validate(workspace) for workspace in workspaces]

    async def get_for_account(self, account: Account, workspace_public_id: str) -> WorkspaceRead:
        workspace = await self.repository.get_owned(workspace_public_id, account.id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return WorkspaceRead.model_validate(workspace)

    async def rename_for_account(
        self, account: Account, workspace_public_id: str, payload: WorkspaceUpdate
    ) -> WorkspaceRead:
        workspace = await self.repository.get_owned(workspace_public_id, account.id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            try:
                workspace = await self.repository.update_name(workspace, data["name"])
            except IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Workspace with this name already exists",
                )

        return WorkspaceRead.model_validate(workspace)

    async def delete_for_account(self, account: Account, workspace_public_id: str) -> None:
        workspace = await self.repository.get_owned(workspace_public_id, account.id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        count = await self.repository.count_owned(account.id)
        if count == 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete the last workspace")
        await self.repository.delete(workspace)
