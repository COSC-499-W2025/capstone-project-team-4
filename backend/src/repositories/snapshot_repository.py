"""Repository for project snapshots."""

from sqlalchemy import desc, select

from src.models.orm.project_snapshot import ProjectSnapshot
from src.repositories.base import BaseRepository


class SnapshotRepository(BaseRepository[ProjectSnapshot]):
    """Snapshot repository."""

    def __init__(self, db):
        super().__init__(ProjectSnapshot, db)

    def get_latest_for_project(self, project_id: int, snapshot_type: str = "midpoint") -> ProjectSnapshot | None:
        stmt = (
            select(ProjectSnapshot)
            .where(ProjectSnapshot.project_id == project_id)
            .where(ProjectSnapshot.snapshot_type == snapshot_type)
            .order_by(desc(ProjectSnapshot.created_at))
            .limit(1)
        )
        return self.db.scalar(stmt)

