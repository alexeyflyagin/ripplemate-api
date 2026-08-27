from fastapi import HTTPException, status

from app.models.account import Account
from app.models.workspace import Workspace
from app.repositories.card import CardRepository
from app.repositories.category import CategoryRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.card import CardCreate, CardListResponse, CardRead, CardUpdate


class CardService:
    def __init__(
        self,
        repository: CardRepository,
        category_repository: CategoryRepository,
        workspace_repository: WorkspaceRepository,
    ):
        self.repository = repository
        self.category_repository = category_repository
        self.workspace_repository = workspace_repository

    async def _resolve_owned_workspace(
        self, account: Account, workspace_public_id: str
    ) -> Workspace:
        workspace = await self.workspace_repository.get_owned(workspace_public_id, account.id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return workspace

    async def _resolve_category_id(
        self, category_public_id: str | None, workspace_id: int
    ) -> int | None:
        if category_public_id is None:
            return None
        category = await self.category_repository.get_in_workspace(
            category_public_id, workspace_id
        )
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category.id

    async def create_in_workspace(
        self, account: Account, workspace_public_id: str, payload: CardCreate
    ) -> CardRead:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        category_id = await self._resolve_category_id(payload.category_id, workspace.id)

        card = await self.repository.create(workspace.id, payload.term, category_id)
        return CardRead.model_validate(card)

    async def list_in_workspace(
        self,
        account: Account,
        workspace_public_id: str,
        category_public_id: str | None,
        search: str | None,
        limit: int,
        offset: int,
        is_favorite: bool | None,
    ) -> CardListResponse:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        category_id = await self._resolve_category_id(category_public_id, workspace.id)

        cards, total = await self.repository.list_in_workspace(
            workspace.id, category_id, search, limit, offset, is_favorite
        )
        return CardListResponse(
            items=[CardRead.model_validate(card) for card in cards],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_in_workspace(
        self, account: Account, workspace_public_id: str, card_public_id: str
    ) -> CardRead:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        card = await self.repository.get_in_workspace(card_public_id, workspace.id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        return CardRead.model_validate(card)

    async def get_random_in_workspace(
        self, account: Account, workspace_public_id: str, category_public_id: str | None
    ) -> CardRead:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        category_id = await self._resolve_category_id(category_public_id, workspace.id)

        card = await self.repository.get_random_in_workspace(workspace.id, category_id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cards found")
        return CardRead.model_validate(card)

    async def update_in_workspace(
        self, account: Account, workspace_public_id: str, card_public_id: str, payload: CardUpdate
    ) -> CardRead:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        card = await self.repository.get_in_workspace(card_public_id, workspace.id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")

        data = payload.model_dump(exclude_unset=True)
        if "category_id" in data:
            data["category_id"] = await self._resolve_category_id(
                data["category_id"], workspace.id
            )

        if data:
            card = await self.repository.update(card, data)

        return CardRead.model_validate(card)

    async def delete_in_workspace(
        self, account: Account, workspace_public_id: str, card_public_id: str
    ) -> None:
        workspace = await self._resolve_owned_workspace(account, workspace_public_id)
        card = await self.repository.get_in_workspace(card_public_id, workspace.id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        await self.repository.delete(card)
