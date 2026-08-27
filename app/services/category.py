from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.account import Account
from app.models.workspace import Workspace
from app.repositories.category import CategoryRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate


class CategoryService:
    def __init__(self, repository: CategoryRepository, workspace_repository: WorkspaceRepository):
        self.repository = repository
        self.workspace_repository = workspace_repository

    async def _resolve_owned_workspace(
        self, account: Account, workspace_public_id: str
    ) -> Workspace:
        workspace = await self.workspace_repository.get_owned(workspace_public_id, account.id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return workspace

    async def create_in_workspace(
        self, account: Account, workspace_public_id: str, payload: CategoryCreate
    ) -> CategoryRead:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        try:
            category = await self.repository.create(workspace.id, payload.name)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this name already exists in this workspace",
            )
        return CategoryRead.model_validate(category)

    async def list_in_workspace(
        self, account: Account, workspace_public_id: str
    ) -> list[CategoryRead]:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        categories = await self.repository.list_in_workspace(workspace.id)
        return [CategoryRead.model_validate(category) for category in categories]

    async def get_in_workspace(
        self, account: Account, workspace_public_id: str, category_public_id: str
    ) -> CategoryRead:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        category = await self.repository.get_in_workspace(category_public_id, workspace.id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return CategoryRead.model_validate(category)

    async def rename_in_workspace(
        self, account: Account, workspace_public_id: str, category_public_id: str, payload: CategoryUpdate
    ) -> CategoryRead:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        category = await self.repository.get_in_workspace(category_public_id, workspace.id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            try:
                category = await self.repository.update_name(category, data["name"])
            except IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Category with this name already exists in this workspace",
                )

        return CategoryRead.model_validate(category)

    async def delete_in_workspace(
        self, account: Account, workspace_public_id: str, category_public_id: str
    ) -> None:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        category = await self.repository.get_in_workspace(category_public_id, workspace.id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        await self.repository.delete(category)
