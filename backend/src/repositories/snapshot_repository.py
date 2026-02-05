"""Repository for Snapshot database operations."""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from src.models.orm import Snapshot, Project


class SnapshotRepository:
    """Repository for managing snapshot database operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def get(self, snapshot_id: int) -> Optional[Snapshot]:
        """Get a snapshot by ID with its relationships loaded."""
        return (
            self.db.query(Snapshot)
            .options(
                joinedload(Snapshot.source_project),
                joinedload(Snapshot.analyzed_project)
            )
            .filter(Snapshot.id == snapshot_id)
            .first()
        )

    def get_by_source_project(self, source_project_id: int) -> List[Snapshot]:
        """Get all snapshots for a source project."""
        return (
            self.db.query(Snapshot)
            .options(joinedload(Snapshot.analyzed_project))
            .filter(Snapshot.source_project_id == source_project_id)
            .order_by(Snapshot.snapshot_date.desc())
            .all()
        )

    def list_all(self, limit: int = 100, offset: int = 0) -> List[Snapshot]:
        """List all snapshots with pagination."""
        return (
            self.db.query(Snapshot)
            .options(
                joinedload(Snapshot.source_project),
                joinedload(Snapshot.analyzed_project)
            )
            .order_by(Snapshot.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count(self) -> int:
        """Count total snapshots."""
        return self.db.query(Snapshot).count()

    def count_by_source_project(self, source_project_id: int) -> int:
        """Count snapshots for a source project."""
        return (
            self.db.query(Snapshot)
            .filter(Snapshot.source_project_id == source_project_id)
            .count()
        )

    def delete(self, snapshot_id: int) -> bool:
        """Delete a snapshot and its analyzed project (cascade)."""
        snapshot = self.get(snapshot_id)
        if not snapshot:
            return False

        self.db.delete(snapshot)
        self.db.commit()
        return True

    def create(self, snapshot: Snapshot) -> Snapshot:
        """Create a new snapshot."""
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def update(self, snapshot_id: int, data: dict) -> Optional[Snapshot]:
        """Update snapshot fields."""
        snapshot = self.get(snapshot_id)
        if not snapshot:
            return None

        for key, value in data.items():
            if hasattr(snapshot, key):
                setattr(snapshot, key, value)

        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot
