"""Portfolio ORM model for storing generated user portfolios."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.user import User


class Portfolio(Base):
    """Portfolio model representing a generated user portfolio."""

    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Portfolio metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Generated portfolio content stored as JSON
    content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="portfolios")

    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, title='{self.title}')>"
