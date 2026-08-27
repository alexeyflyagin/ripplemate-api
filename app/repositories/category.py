from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, workspace_id: int, name: str) -> Category:
        category = Category(workspace_id=workspace_id, name=name)
        self.session.add(category)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(category)
        return category

    async def get_in_workspace(
        self, category_public_id: str, workspace_id: int
    ) -> Category | None:
        result = await self.session.execute(
            select(Category).where(
                Category.public_id == category_public_id,
                Category.workspace_id == workspace_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_in_workspace(self, workspace_id: int) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .where(Category.workspace_id == workspace_id)
            .order_by(Category.created_at)
        )
        return list(result.scalars().all())

    async def update_name(self, category: Category, name: str) -> Category:
        category.name = name
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self.session.delete(category)
        await self.session.commit()
