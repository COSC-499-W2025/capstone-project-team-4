"""Data privacy settings ORM model for user AI consent management."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.user import User


class DataPrivacySettings(Base):
    """Data privacy settings model for managing user AI consent preferences."""

    __tablename__ = "data_privacy_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # AI consent settings
    allow_ai_analysis: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_ai_resume_generation: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_data_collection: Mapped[bool] = mapped_column(Boolean, default=False)

    # Consent tracking
    consent_given_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="privacy_settings")

    def __repr__(self) -> str:
        return f"<DataPrivacySettings(id={self.id}, user_id={self.user_id}, ai_analysis={self.allow_ai_analysis})>"
