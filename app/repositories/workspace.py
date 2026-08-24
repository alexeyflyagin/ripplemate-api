from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace


class WorkspaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, owner_id: int, name: str) -> Workspace:
        workspace = Workspace(owner_id=owner_id, name=name)
        self.session.add(workspace)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(workspace)
        return workspace

    async def get_owned(self, workspace_id: int, owner_id: int) -> Workspace | None:
        result = await self.session.execute(
            select(Workspace).where(
                Workspace.id == workspace_id, Workspace.owner_id == owner_id
            )
        )
        return result.scalar_one_or_none()

    async def update_name(self, workspace: Workspace, name: str) -> Workspace:
        workspace.name = name
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(workspace)
        return workspace

    async def list_owned(self, owner_id: int) -> list[Workspace]:
        result = await self.session.execute(
            select(Workspace).where(Workspace.owner_id == owner_id).order_by(Workspace.created_at)
        )
        return list(result.scalars().all())

    async def count_owned(self, owner_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Workspace.id)).where(
                Workspace.owner_id == owner_id
            )
        )
        return result.scalar_one()

    async def delete(self, workspace: Workspace) -> None:
        await self.session.delete(workspace)
        await self.session.commit()
