"""Tool ORM models."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project


class Tool(Base):
    """Tool lookup table for normalization."""

    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Tool(id={self.id}, name='{self.name}', category='{self.category}')>"


class ProjectTool(Base):
    """ProjectTool model representing tools detected in a project."""

    __tablename__ = "project_tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tools.id"), nullable=False, index=True
    )
    detection_score: Mapped[float] = mapped_column(Float, default=1.0)
    config_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tools")
    tool: Mapped["Tool"] = relationship("Tool")

    __table_args__ = (
        UniqueConstraint("project_id", "tool_id", name="uq_project_tool"),
    )

    def __repr__(self) -> str:
        return f"<ProjectTool(project_id={self.project_id}, tool='{self.tool_id}', score={self.detection_score})>"
