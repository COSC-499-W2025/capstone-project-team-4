"""Library ORM models."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project


class Library(Base):
    """Library lookup table for normalization."""

    __tablename__ = "libraries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ecosystem: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("name", "ecosystem", name="uq_library_name_ecosystem"),
    )

    def __repr__(self) -> str:
        return (
            f"<Library(id={self.id}, name='{self.name}', ecosystem='{self.ecosystem}')>"
        )


class ProjectLibrary(Base):
    """ProjectLibrary model representing libraries used in a project."""

    __tablename__ = "project_libraries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    library_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("libraries.id"), nullable=False, index=True
    )
    version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_dev_dependency: Mapped[bool] = mapped_column(Boolean, default=False)
    detection_score: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="libraries")
    library: Mapped["Library"] = relationship("Library")

    __table_args__ = (
        UniqueConstraint("project_id", "library_id", name="uq_project_library"),
    )

    def __repr__(self) -> str:
        return f"<ProjectLibrary(project_id={self.project_id}, library='{self.library_id}', version='{self.version}')>"
