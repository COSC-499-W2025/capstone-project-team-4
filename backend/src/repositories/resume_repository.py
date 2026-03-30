"""Resume repository for database operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.orm.resume import ResumeItem
from src.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[ResumeItem]):
    """Repository for resume item operations."""

    def __init__(self, db: Session):
        """Initialize resume repository."""
        super().__init__(ResumeItem, db)

    def get_by_project(self, project_id: int) -> List[ResumeItem]:
        """Get all resume items for a project."""
        stmt = (
            select(ResumeItem)
            .where(ResumeItem.project_id == project_id)
            .order_by(ResumeItem.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_latest(self, project_id: int) -> Optional[ResumeItem]:
        """Get the most recent resume item for a project."""
        stmt = (
            select(ResumeItem)
            .where(ResumeItem.project_id == project_id)
            .order_by(ResumeItem.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def create_resume_item(
        self,
        project_id: int,
        title: str,
        highlights: List[str],
    ) -> ResumeItem:
        """Create a new resume item."""
        resume_item = ResumeItem(
            project_id=project_id,
            title=title,
            highlights=highlights,
        )
        return self.create(resume_item)

    def update_resume_item(
        self,
        resume_id: int,
        title: Optional[str] = None,
        highlights: Optional[List[str]] = None,
    ) -> Optional[ResumeItem]:
        """Update an existing resume item."""
        resume_item = self.get(resume_id)
        if not resume_item:
            return None

        if title is not None:
            resume_item.title = title
        if highlights is not None:
            resume_item.highlights = highlights

        return self.update(resume_item)

    def delete_by_project(self, project_id: int) -> int:
        """Delete all resume items for a project."""
        from sqlalchemy import delete

        stmt = delete(ResumeItem).where(ResumeItem.project_id == project_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
