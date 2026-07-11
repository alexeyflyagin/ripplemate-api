import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.settings import Settings


class Account(Base):
    __tablename__ = "account"
    __table_args__ = (
        CheckConstraint("length(trim(display_name)) > 0", name="ck_account_display_name_not_blank"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
    settings_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("settings.id"), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(32), nullable=False)

    settings: Mapped["Settings"] = relationship(cascade="all, delete-orphan", single_parent=True)
