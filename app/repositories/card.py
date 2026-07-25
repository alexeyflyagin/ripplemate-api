from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card


class CardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, workspace_id: int, term: str, category_id: int | None) -> Card:
        card = Card(workspace_id=workspace_id, term=term, category_id=category_id)
        self.session.add(card)
        await self.session.commit()
        await self.session.refresh(card)
        return card

    async def get_in_workspace(self, card_id: int, workspace_id: int) -> Card | None:
        result = await self.session.execute(
            select(Card).where(Card.id == card_id, Card.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def list_in_workspace(
            self,
            workspace_id: int,
            category_id: int | None,
            search: str | None,
            limit: int,
            offset: int,
    ) -> tuple[list[Card], int]:
        conditions = [Card.workspace_id == workspace_id]
        if category_id is not None:
            conditions.append(Card.category_id == category_id)
        if search is not None:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            conditions.append(Card.term.ilike(f"%{escaped}%", escape="\\"))

        count_result = await self.session.execute(
            select(func.count()).select_from(Card).where(*conditions)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Card).where(*conditions).order_by(Card.created_at.desc()).limit(limit).offset(offset)
        )
        cards = list(result.scalars().all())

        return cards, total

    async def get_random_in_workspace(self, workspace_id: int, category_id: int | None) -> Card | None:
        conditions = [Card.workspace_id == workspace_id]
        if category_id is not None:
            conditions.append(Card.category_id == category_id)

        result = await self.session.execute(
            select(Card).where(*conditions).order_by(func.random()).limit(1)
        )
        return result.scalar_one_or_none()

    async def update(self, card: Card, data: dict) -> Card:
        for field, value in data.items():
            setattr(card, field, value)
        await self.session.commit()
        await self.session.refresh(card)
        return card

    async def delete(self, card: Card) -> None:
        await self.session.delete(card)
        await self.session.commit()
