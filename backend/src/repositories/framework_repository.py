"""Framework repository for database operations."""

import json
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.orm.framework import Framework, ProjectFramework
from src.repositories.base import BaseRepository


class FrameworkRepository(BaseRepository[ProjectFramework]):
    """Repository for framework operations."""

    def __init__(self, db: Session):
        """Initialize framework repository."""
        super().__init__(ProjectFramework, db)

    def get_or_create_framework(self, name: str) -> Framework:
        """Get existing framework or create a new one."""
        stmt = select(Framework).where(Framework.name == name)
        existing = self.db.scalar(stmt)
        if existing:
            return existing

        framework = Framework(name=name)
        self.db.add(framework)
        self.db.commit()
        self.db.refresh(framework)
        return framework

    def get_by_project(self, project_id: int) -> List[ProjectFramework]:
        """Get all frameworks for a project."""
        stmt = (
            select(ProjectFramework)
            .where(ProjectFramework.project_id == project_id)
            .order_by(ProjectFramework.framework_id)
        )
        return list(self.db.scalars(stmt).all())

    def create_project_framework(
        self,
        project_id: int,
        framework_id: int,
        detection_score: float = 1.0,
        original_score: float = 1.0,
        cross_validation_boost: Optional[float] = None,
        validation_sources: Optional[str] = None,
        is_gap_filled: bool = False,
    ) -> ProjectFramework:
        """Create a new project framework association."""
        existing = self.db.scalar(
            select(ProjectFramework)
            .where(ProjectFramework.project_id == project_id)
            .where(ProjectFramework.framework_id == framework_id)
        )
        if existing:
            existing.detection_score = detection_score
            existing.original_score = original_score
            existing.cross_validation_boost = cross_validation_boost
            existing.validation_sources = validation_sources
            existing.is_gap_filled = is_gap_filled
            self.db.commit()
            self.db.refresh(existing)
            return existing

        project_framework = ProjectFramework(
            project_id=project_id,
            framework_id=framework_id,
            detection_score=detection_score,
            original_score=original_score,
            cross_validation_boost=cross_validation_boost,
            validation_sources=validation_sources,
            is_gap_filled=is_gap_filled,
        )
        return self.create(project_framework)

    def create_frameworks_bulk(
        self, frameworks_data: List[dict], project_id: int
    ) -> List[ProjectFramework]:
        """Create multiple frameworks efficiently."""
        project_frameworks = []
        seen = set()

        for data in frameworks_data:
            name = data.get("name", "").strip()
            if not name:
                continue

            key = name.lower()
            if key in seen:
                continue
            seen.add(key)

            framework = self.get_or_create_framework(name=name)

            existing = self.db.scalar(
                select(ProjectFramework)
                .where(ProjectFramework.project_id == project_id)
                .where(ProjectFramework.framework_id == framework.id)
            )
            if existing:
                continue

            # Convert validation_sources list to JSON string
            validation_sources = data.get("validation_sources")
            if isinstance(validation_sources, list):
                validation_sources = json.dumps(validation_sources) if validation_sources else None

            project_framework = ProjectFramework(
                project_id=project_id,
                framework_id=framework.id,
                detection_score=data.get("confidence", 1.0),
                original_score=data.get("original_score", 1.0),
                cross_validation_boost=data.get("cross_validation_boost"),
                validation_sources=validation_sources,
                is_gap_filled=data.get("is_gap_filled", False),
            )
            project_frameworks.append(project_framework)

        if project_frameworks:
            return self.create_many(project_frameworks)
        return []

    def count_by_project(self, project_id: int) -> int:
        """Count frameworks in a project."""
        stmt = select(func.count(ProjectFramework.id)).where(
            ProjectFramework.project_id == project_id
        )
        return self.db.scalar(stmt) or 0

    def delete_by_project(self, project_id: int) -> int:
        """Delete all frameworks for a project."""
        stmt = select(ProjectFramework).where(ProjectFramework.project_id == project_id)
        frameworks = list(self.db.scalars(stmt).all())
        count = len(frameworks)
        for fw in frameworks:
            self.db.delete(fw)
        self.db.commit()
        return count

    def get_framework_names(self, project_id: int) -> List[str]:
        """Get all framework names for a project."""
        stmt = (
            select(Framework.name)
            .join(ProjectFramework)
            .where(ProjectFramework.project_id == project_id)
            .order_by(Framework.name)
        )
        return list(self.db.scalars(stmt).all())
