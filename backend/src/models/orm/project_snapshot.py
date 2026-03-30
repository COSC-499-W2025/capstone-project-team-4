"""Project snapshot ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project


class ProjectSnapshot(Base):
    """Stored snapshot metadata and payload."""

    __tablename__ = "project_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    commit_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    commit_index: Mapped[int] = mapped_column(Integer, nullable=False)
    total_commits: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="snapshots")
