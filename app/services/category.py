from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.account import Account
from app.repositories.category import CategoryRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate


class CategoryService:
    def __init__(self, repository: CategoryRepository, workspace_repository: WorkspaceRepository):
        self.repository = repository
        self.workspace_repository = workspace_repository

    async def _ensure_owned_workspace(self, account: Account, workspace_id: int) -> None:
        workspace = await self.workspace_repository.get_owned(workspace_id, account.id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    async def create_in_workspace(
            self, account: Account, workspace_id: int, payload: CategoryCreate
    ) -> CategoryRead:
        await self._ensure_owned_workspace(account, workspace_id)
        try:
            category = await self.repository.create(workspace_id, payload.name)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this name already exists in this workspace",
            )
        return CategoryRead.model_validate(category)

    async def list_in_workspace(self, account: Account, workspace_id: int) -> list[CategoryRead]:
        await self._ensure_owned_workspace(account, workspace_id)
        categories = await self.repository.list_in_workspace(workspace_id)
        return [CategoryRead.model_validate(category) for category in categories]

    async def get_in_workspace(
            self, account: Account, workspace_id: int, category_id: int
    ) -> CategoryRead:
        await self._ensure_owned_workspace(account, workspace_id)
        category = await self.repository.get_in_workspace(category_id, workspace_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return CategoryRead.model_validate(category)

    async def rename_in_workspace(
            self, account: Account, workspace_id: int, category_id: int, payload: CategoryUpdate
    ) -> CategoryRead:
        await self._ensure_owned_workspace(account, workspace_id)
        category = await self.repository.get_in_workspace(category_id, workspace_id)
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
            self, account: Account, workspace_id: int, category_id: int
    ) -> None:
        await self._ensure_owned_workspace(account, workspace_id)
        category = await self.repository.get_in_workspace(category_id, workspace_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        await self.repository.delete(category)
