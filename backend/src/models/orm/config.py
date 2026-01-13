"""Config ORM model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class Config(Base):
    """Config model for storing application configuration."""

    __tablename__ = "config"

    key: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Config(key='{self.key}')>"
