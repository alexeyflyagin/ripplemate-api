from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Card(Base):
    __tablename__ = "card"
    __table_args__ = (
        CheckConstraint("length(trim(term)) > 0", name="ck_card_term_not_blank"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("category.id", ondelete="CASCADE"), nullable=True
    )
    term: Mapped[str] = mapped_column(String(255), nullable=False)