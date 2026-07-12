from fastapi import HTTPException, status

from app.models.account import Account
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

    async def _ensure_owned_workspace(self, account: Account, workspace_id: int) -> None:
        workspace = await self.workspace_repository.get_owned(workspace_id, account.id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    async def _ensure_valid_category(self, workspace_id: int, category_id: int | None) -> None:
        if category_id is None:
            return
        category = await self.category_repository.get_in_workspace(category_id, workspace_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    async def create_in_workspace(
            self, account: Account, workspace_id: int, payload: CardCreate
    ) -> CardRead:
        await self._ensure_owned_workspace(account, workspace_id)
        await self._ensure_valid_category(workspace_id, payload.category_id)

        card = await self.repository.create(workspace_id, payload.term, payload.category_id)
        return CardRead.model_validate(card)

    async def list_in_workspace(
            self,
            account: Account,
            workspace_id: int,
            category_id: int | None,
            search: str | None,
            limit: int,
            offset: int,
    ) -> CardListResponse:
        await self._ensure_owned_workspace(account, workspace_id)
        await self._ensure_valid_category(workspace_id, category_id)

        cards, total = await self.repository.list_in_workspace(
            workspace_id, category_id, search, limit, offset
        )
        return CardListResponse(
            items=[CardRead.model_validate(card) for card in cards],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_in_workspace(self, account: Account, workspace_id: int, card_id: int) -> CardRead:
        await self._ensure_owned_workspace(account, workspace_id)
        card = await self.repository.get_in_workspace(card_id, workspace_id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        return CardRead.model_validate(card)

    async def get_random_in_workspace(
            self, account: Account, workspace_id: int, category_id: int | None
    ) -> CardRead:
        await self._ensure_owned_workspace(account, workspace_id)
        await self._ensure_valid_category(workspace_id, category_id)

        card = await self.repository.get_random_in_workspace(workspace_id, category_id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cards found")
        return CardRead.model_validate(card)

    async def update_in_workspace(
            self, account: Account, workspace_id: int, card_id: int, payload: CardUpdate
    ) -> CardRead:
        await self._ensure_owned_workspace(account, workspace_id)
        card = await self.repository.get_in_workspace(card_id, workspace_id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")

        data = payload.model_dump(exclude_unset=True)
        if "category_id" in data:
            await self._ensure_valid_category(workspace_id, data["category_id"])

        if data:
            card = await self.repository.update(card, data)

        return CardRead.model_validate(card)

    async def delete_in_workspace(self, account: Account, workspace_id: int, card_id: int) -> None:
        await self._ensure_owned_workspace(account, workspace_id)
        card = await self.repository.get_in_workspace(card_id, workspace_id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        await self.repository.delete(card)
