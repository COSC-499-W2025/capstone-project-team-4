"""Repository for snapshot comparisons."""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.models.orm.snapshot_comparison import SnapshotComparison
from src.repositories.base import BaseRepository


class SnapshotComparisonRepository(BaseRepository[SnapshotComparison]):
    """Snapshot comparison repository."""

    def __init__(self, db: Session):
        super().__init__(SnapshotComparison, db)

    def get_latest_for_project(self, project_id: int) -> SnapshotComparison | None:
        stmt = (
            select(SnapshotComparison)
            .where(SnapshotComparison.project_id == project_id)
            .order_by(desc(SnapshotComparison.created_at))
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_by_snapshot_ids(
        self, current_snapshot_id: int, midpoint_snapshot_id: int
    ) -> SnapshotComparison | None:
        stmt = (
            select(SnapshotComparison)
            .where(SnapshotComparison.current_snapshot_id == current_snapshot_id)
            .where(SnapshotComparison.midpoint_snapshot_id == midpoint_snapshot_id)
            .limit(1)
        )
        return self.db.scalar(stmt)
