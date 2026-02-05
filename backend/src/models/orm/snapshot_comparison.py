"""Snapshot comparison ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.snapshot import Snapshot


class SnapshotComparison(Base):
    """Model for storing snapshot comparison results."""

    __tablename__ = "snapshot_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # References to the two snapshots being compared
    snapshot1_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot2_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True
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
    snapshot1: Mapped["Snapshot"] = relationship(
        "Snapshot",
        foreign_keys=[snapshot1_id],
        back_populates="comparisons_as_snapshot1"
    )
    snapshot2: Mapped["Snapshot"] = relationship(
        "Snapshot",
        foreign_keys=[snapshot2_id],
        back_populates="comparisons_as_snapshot2"
    )

    def __repr__(self) -> str:
        return f"<SnapshotComparison(id={self.id}, snapshot1_id={self.snapshot1_id}, snapshot2_id={self.snapshot2_id})>"
