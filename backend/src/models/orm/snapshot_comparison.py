"""Snapshot comparison ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project


class SnapshotComparison(Base):
    """Model for storing snapshot comparison results."""

    __tablename__ = "snapshot_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # References to the two projects being compared
    snapshot1_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot2_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Comparison metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Metric changes (stored as JSON for flexibility)
    metric_changes: Mapped[dict] = mapped_column(JSON, nullable=False)

    # New items detected
    new_languages: Mapped[list] = mapped_column(JSON, default=list)
    new_frameworks: Mapped[list] = mapped_column(JSON, default=list)
    new_libraries: Mapped[list] = mapped_column(JSON, default=list)
    new_contributors: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships
    snapshot1: Mapped["Project"] = relationship(
        "Project", foreign_keys=[snapshot1_id], uselist=False
    )
    snapshot2: Mapped["Project"] = relationship(
        "Project", foreign_keys=[snapshot2_id], uselist=False
    )

    def __repr__(self) -> str:
        return f"<SnapshotComparison(id={self.id}, snapshot1_id={self.snapshot1_id}, snapshot2_id={self.snapshot2_id})>"
