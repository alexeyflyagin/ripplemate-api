from datetime import datetime

from sqlalchemy import CheckConstraint, String, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Settings(Base):
    __tablename__ = "settings"
    __table_args__ = (
        CheckConstraint("font IN ('serif', 'sans-serif')", name="ck_settings_font"),
        CheckConstraint("language IN ('ru', 'en', 'auto')", name="ck_settings_language"),
        CheckConstraint("theme IN ('dark', 'light', 'auto')", name="ck_settings_theme"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
    font: Mapped[str] = mapped_column(String(10), server_default="sans-serif", nullable=False)
    language: Mapped[str] = mapped_column(String(4), server_default="auto", nullable=False)
    theme: Mapped[str] = mapped_column(String(10), server_default="auto", nullable=False)
