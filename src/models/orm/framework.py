"""Framework ORM models."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project


class Framework(Base):
    """Framework lookup table for normalization."""

    __tablename__ = "frameworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Framework(id={self.id}, name='{self.name}')>"


class ProjectFramework(Base):
    """ProjectFramework model representing frameworks detected in a project."""

    __tablename__ = "project_frameworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    framework_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("frameworks.id"), nullable=False, index=True
    )
    detection_score: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="frameworks")
    framework: Mapped["Framework"] = relationship("Framework")

    __table_args__ = (
        UniqueConstraint("project_id", "framework_id", name="uq_project_framework"),
    )

    def __repr__(self) -> str:
        return f"<ProjectFramework(project_id={self.project_id}, framework_id={self.framework_id})>"
