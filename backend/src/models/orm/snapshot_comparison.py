"""Snapshot comparison ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project
    from src.models.orm.project_snapshot import ProjectSnapshot


class SnapshotComparison(Base):
    """Stored comparison between current and midpoint snapshots."""

    __tablename__ = "snapshot_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    midpoint_snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    project: Mapped["Project"] = relationship("Project")
    current_snapshot: Mapped["ProjectSnapshot"] = relationship(
        "ProjectSnapshot", foreign_keys=[current_snapshot_id]
    )
    midpoint_snapshot: Mapped["ProjectSnapshot"] = relationship(
        "ProjectSnapshot", foreign_keys=[midpoint_snapshot_id]
    )
