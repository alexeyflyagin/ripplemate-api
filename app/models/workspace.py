from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Workspace(Base):
    __tablename__ = "workspace"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_workspace_name_not_blank"),
        UniqueConstraint("owner_id", "name", name="uq_workspace_owner_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    name: Mapped[str] = mapped_column(String(24), nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id", ondelete="CASCADE"), nullable=False)