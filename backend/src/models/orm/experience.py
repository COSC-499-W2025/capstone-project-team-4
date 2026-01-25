"""Experience ORM model for storing all types of experience history."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.user import User


class ExperienceType(str, Enum):
    """Enum for different types of experiences."""

    WORK = "work"
    EDUCATION = "education"
    VOLUNTEER = "volunteer"
    CERTIFICATION = "certification"
    PROJECT = "project"


class Experience(Base):
    """Experience model for storing all types of experience history (work, education, etc.)."""

    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Experience type
    experience_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ExperienceType.WORK.value, index=True
    )

    # Organization/Company details
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)

    # Duration
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    achievements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="experiences")

    def __repr__(self) -> str:
        return f"<Experience(id={self.id}, type='{self.experience_type}', company='{self.company_name}', title='{self.job_title}')>"
