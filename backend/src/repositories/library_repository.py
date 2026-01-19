"""Library repository for database operations."""

from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.orm.library import Library, ProjectLibrary
from src.repositories.base import BaseRepository


class LibraryRepository(BaseRepository[ProjectLibrary]):
    """Repository for library operations."""

    def __init__(self, db: Session):
        """Initialize library repository."""
        super().__init__(ProjectLibrary, db)

    def get_or_create_library(self, name: str, ecosystem: str) -> Library:
        """Get existing library or create a new one."""
        stmt = select(Library).where(Library.name == name)
        existing = self.db.scalar(stmt)
        if existing:
            return existing

        library = Library(name=name, ecosystem=ecosystem)
        self.db.add(library)
        self.db.commit()
        self.db.refresh(library)
        return library

    def get_by_project(self, project_id: int) -> List[ProjectLibrary]:
        """Get all libraries for a project."""
        stmt = (
            select(ProjectLibrary)
            .where(ProjectLibrary.project_id == project_id)
            .order_by(ProjectLibrary.library_id)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_ecosystem(self, project_id: int, ecosystem: str) -> List[ProjectLibrary]:
        """Get libraries by ecosystem for a project."""
        stmt = (
            select(ProjectLibrary)
            .join(Library)
            .where(ProjectLibrary.project_id == project_id)
            .where(Library.ecosystem == ecosystem)
        )
        return list(self.db.scalars(stmt).all())

    def get_grouped_by_ecosystem(self, project_id: int) -> Dict[str, List[ProjectLibrary]]:
        """Get libraries grouped by ecosystem."""
        libraries = self.get_by_project(project_id)
        grouped: Dict[str, List[ProjectLibrary]] = {}
        for proj_lib in libraries:
            ecosystem = proj_lib.library.ecosystem
            if ecosystem not in grouped:
                grouped[ecosystem] = []
            grouped[ecosystem].append(proj_lib)
        return grouped

    def get_ecosystems(self, project_id: int) -> List[str]:
        """Get all unique ecosystems for a project."""
        stmt = (
            select(Library.ecosystem)
            .join(ProjectLibrary)
            .where(ProjectLibrary.project_id == project_id)
            .distinct()
        )
        return list(self.db.scalars(stmt).all())

    def create_project_library(
        self,
        project_id: int,
        library_id: int,
        version: Optional[str] = None,
        is_dev_dependency: bool = False,
        detection_score: float = 1.0,
    ) -> ProjectLibrary:
        """Create a new project library association."""
        # Check if association already exists
        existing = self.db.scalar(
            select(ProjectLibrary)
            .where(ProjectLibrary.project_id == project_id)
            .where(ProjectLibrary.library_id == library_id)
        )
        if existing:
            # Update version if provided
            if version:
                existing.version = version
            self.db.commit()
            self.db.refresh(existing)
            return existing

        project_library = ProjectLibrary(
            project_id=project_id,
            library_id=library_id,
            version=version,
            is_dev_dependency=is_dev_dependency,
            detection_score=detection_score,
        )
        return self.create(project_library)

    def create_libraries_bulk(self, libraries_data: List[dict], project_id: int) -> List[ProjectLibrary]:
        """Create multiple libraries efficiently."""
        project_libraries = []
        seen = set()

        for data in libraries_data:
            name = data.get("name", "").strip()
            if not name:
                continue

            # Deduplicate by name within this batch
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)

            # Get or create the library lookup record
            library = self.get_or_create_library(
                name=name,
                ecosystem=data.get("ecosystem", "unknown")
            )

            # Check if project-library association exists
            existing = self.db.scalar(
                select(ProjectLibrary)
                .where(ProjectLibrary.project_id == project_id)
                .where(ProjectLibrary.library_id == library.id)
            )
            if existing:
                continue

            project_library = ProjectLibrary(
                project_id=project_id,
                library_id=library.id,
                version=data.get("version"),
                is_dev_dependency=data.get("is_dev_dependency", False),
                detection_score=data.get("detection_score", 1.0),
            )
            project_libraries.append(project_library)

        if project_libraries:
            return self.create_many(project_libraries)
        return []

    def count_by_project(self, project_id: int) -> int:
        """Count libraries in a project."""
        stmt = select(func.count(ProjectLibrary.id)).where(ProjectLibrary.project_id == project_id)
        return self.db.scalar(stmt) or 0

    def count_by_ecosystem(self, project_id: int) -> Dict[str, int]:
        """Count libraries by ecosystem for a project."""
        stmt = (
            select(Library.ecosystem, func.count(ProjectLibrary.id))
            .join(Library)
            .where(ProjectLibrary.project_id == project_id)
            .group_by(Library.ecosystem)
        )
        result = self.db.execute(stmt).all()
        return {row[0]: row[1] for row in result}

    def delete_by_project(self, project_id: int) -> int:
        """Delete all libraries for a project."""
        stmt = select(ProjectLibrary).where(ProjectLibrary.project_id == project_id)
        libraries = list(self.db.scalars(stmt).all())
        count = len(libraries)
        for lib in libraries:
            self.db.delete(lib)
        self.db.commit()
        return count

    def get_library_names(self, project_id: int) -> List[str]:
        """Get all library names for a project."""
        stmt = (
            select(Library.name)
            .join(ProjectLibrary)
            .where(ProjectLibrary.project_id == project_id)
            .order_by(Library.name)
        )
        return list(self.db.scalars(stmt).all())
