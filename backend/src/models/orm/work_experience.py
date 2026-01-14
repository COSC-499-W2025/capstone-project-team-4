"""Work experience ORM model for storing employment history."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.user_profile import UserProfile


class WorkExperience(Base):
    """Work experience model for storing employment history."""

    __tablename__ = "work_experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Job details
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Full-time, Part-time, Contract, etc.

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)

    # Duration
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # Null means current job
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Stored as JSON array string
    achievements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Stored as JSON array string

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user_profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="work_experiences")

    def __repr__(self) -> str:
        return f"<WorkExperience(id={self.id}, company='{self.company_name}', title='{self.job_title}')>"
