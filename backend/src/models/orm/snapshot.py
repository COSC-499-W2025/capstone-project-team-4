"""Snapshot ORM model for tracking project snapshots at different points in time."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project
    from src.models.orm.snapshot_comparison import SnapshotComparison


class Snapshot(Base):
    """
    Snapshot model representing a project state at a specific point in time.

    Snapshots are created when analyzing a project with version history,
    allowing comparison of different states (e.g., baseline vs current).
    """

    __tablename__ = "snapshots"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign key to source project
    source_project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Snapshot metadata
    snapshot_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of snapshot: 'baseline', 'current', or custom"
    )

    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When this snapshot was created"
    )

    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User-friendly label (e.g., '2024-02-04 Baseline' or 'Pre-Refactor')"
    )

    # Git-specific metadata (optional)
    commit_hash: Mapped[Optional[str]] = mapped_column(
        String(40),
        nullable=True,
        comment="Git commit hash this snapshot represents"
    )

    commit_percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Percentage through git history (e.g., 50.0 for midpoint)"
    )

    # Additional metadata
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional user description of this snapshot"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    source_project: Mapped["Project"] = relationship(
        "Project",
        foreign_keys=[source_project_id],
        back_populates="snapshots"
    )

    analyzed_project: Mapped[Optional["Project"]] = relationship(
        "Project",
        foreign_keys="Project.snapshot_id",
        back_populates="snapshot",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True
    )

    # Comparisons where this snapshot is involved
    comparisons_as_snapshot1: Mapped[list["SnapshotComparison"]] = relationship(
        "SnapshotComparison",
        foreign_keys="SnapshotComparison.snapshot1_id",
        back_populates="snapshot1",
        cascade="all, delete-orphan"
    )

    comparisons_as_snapshot2: Mapped[list["SnapshotComparison"]] = relationship(
        "SnapshotComparison",
        foreign_keys="SnapshotComparison.snapshot2_id",
        back_populates="snapshot2",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Snapshot(id={self.id}, label='{self.label}', type='{self.snapshot_type}')>"
