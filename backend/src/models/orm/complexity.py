"""Complexity ORM model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project


class Complexity(Base):
    """Complexity model representing function-level complexity metrics."""

    __tablename__ = "complexities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    function_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cyclomatic_complexity: Mapped[int] = mapped_column(Integer, default=1, index=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="complexities")

    def __repr__(self) -> str:
        return f"<Complexity(id={self.id}, function='{self.function_name}', complexity={self.cyclomatic_complexity})>"
