from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, String, func
from nanoid import generate
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.category import Category


class Card(Base):
    __tablename__ = "card"
    __table_args__ = (
        CheckConstraint("length(trim(term)) > 0", name="ck_card_term_not_blank"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(16), unique=True, index=True, nullable=False, default=lambda: generate(size=16)
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("category.id", ondelete="CASCADE"), nullable=True
    )
    term: Mapped[str] = mapped_column(String(255), nullable=False)
    is_favorite: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    category: Mapped[Category | None] = relationship(lazy="joined")
