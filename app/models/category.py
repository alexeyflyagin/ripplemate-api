from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Category(Base):
    __tablename__ = "category"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_category_name_not_blank"),
        UniqueConstraint("workspace_id", "name", name="uq_category_workspace_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    name: Mapped[str] = mapped_column(String(24), nullable=False)
    workspace_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("workspace.id", ondelete="CASCADE"),
                                              nullable=False)
