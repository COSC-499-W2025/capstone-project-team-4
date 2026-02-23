"""User ORM model for authentication and user management."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.user_profile import UserProfile
    from src.models.orm.experience import Experience
    from src.models.orm.project import Project
    from src.models.orm.data_privacy_settings import DataPrivacySettings
    from src.models.orm.portfolio import Portfolio


class User(Base):
    """User model for authentication and account management."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    experiences: Mapped[List["Experience"]] = relationship(
        "Experience", back_populates="user", cascade="all, delete-orphan"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )
    privacy_settings: Mapped[Optional["DataPrivacySettings"]] = relationship(
        "DataPrivacySettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    portfolios: Mapped[List["Portfolio"]] = relationship(
        "Portfolio", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"
