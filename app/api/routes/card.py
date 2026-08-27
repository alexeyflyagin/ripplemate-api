from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.account import Account
from app.repositories.card import CardRepository
from app.repositories.category import CategoryRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.card import CardCreate, CardListResponse, CardRead, CardUpdate
from app.services.card import CardService
from app.users import get_current_account

router = APIRouter()


def get_card_service(session: AsyncSession = Depends(get_session)) -> CardService:
    return CardService(
        CardRepository(session), CategoryRepository(session), WorkspaceRepository(session)
    )


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
async def create_card(
        workspace_id: str,
        payload: CardCreate,
        account: Account = Depends(get_current_account),
        service: CardService = Depends(get_card_service),
):
    return await service.create_in_workspace(account, workspace_id, payload)


@router.get("", response_model=CardListResponse)
async def list_cards(
    workspace_id: str,
    category_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    is_favorite: bool | None = Query(default=None),
    account: Account = Depends(get_current_account),
    service: CardService = Depends(get_card_service),
):
    return await service.list_in_workspace(account, workspace_id, category_id, search, limit, offset, is_favorite)


@router.get("/random", response_model=CardRead)
async def get_random_card(
        workspace_id: str,
        category_id: str | None = Query(default=None),
        account: Account = Depends(get_current_account),
        service: CardService = Depends(get_card_service),
):
    return await service.get_random_in_workspace(account, workspace_id, category_id)


@router.get("/{card_id}", response_model=CardRead)
async def get_card(
        workspace_id: str,
        card_id: str,
        account: Account = Depends(get_current_account),
        service: CardService = Depends(get_card_service),
):
    return await service.get_in_workspace(account, workspace_id, card_id)


@router.patch("/{card_id}", response_model=CardRead)
async def update_card(
        workspace_id: str,
        card_id: str,
        payload: CardUpdate,
        account: Account = Depends(get_current_account),
        service: CardService = Depends(get_card_service),
):
    return await service.update_in_workspace(account, workspace_id, card_id, payload)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
        workspace_id: str,
        card_id: str,
        account: Account = Depends(get_current_account),
        service: CardService = Depends(get_card_service),
):
    await service.delete_in_workspace(account, workspace_id, card_id)
