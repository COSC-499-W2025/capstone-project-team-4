"""Project service for project operations."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.schemas.project import ProjectSummary, ProjectDetail, ProjectList
from src.repositories.project_repository import ProjectRepository
from src.repositories.file_repository import FileRepository
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.complexity_repository import ComplexityRepository
from src.repositories.skill_repository import SkillRepository

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project operations."""

    def __init__(self, db: Session):
        """Initialize project service with database session."""
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.file_repo = FileRepository(db)
        self.contributor_repo = ContributorRepository(db)
        self.complexity_repo = ComplexityRepository(db)
        self.skill_repo = SkillRepository(db)

    def list_projects(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> ProjectList:
        """
        List all projects with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            ProjectList with paginated results
        """
        skip = (page - 1) * page_size
        total = self.project_repo.count()
        pages = (total + page_size - 1) // page_size

        summaries = self.project_repo.get_all_summaries(skip=skip, limit=page_size)

        items = []
        for s in summaries:
            if s:
                items.append(ProjectSummary(
                    id=s["id"],
                    name=s["name"],
                    source_type=s["source_type"],
                    created_at=s["created_at"],
                    zip_uploaded_at=s.get("zip_uploaded_at"),
                    first_file_created=s.get("first_file_created"),
                    first_commit_date=s.get("first_commit_date"),
                    project_started_at=s.get("project_started_at"),
                    file_count=s["file_count"],
                    language_count=s["language_count"],
                    framework_count=s["framework_count"],
                    contributor_count=s["contributor_count"],
                    skill_count=s["skill_count"],
                ))

        return ProjectList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_project(self, project_id: int) -> Optional[ProjectDetail]:
        """
        Get detailed project information.

        Args:
            project_id: ID of the project

        Returns:
            ProjectDetail or None if not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return None

        # Get related data
        languages = self.project_repo.get_languages(project_id)
        frameworks = self.project_repo.get_frameworks(project_id)
        total_loc = self.project_repo.get_total_lines_of_code(project_id)
        complexity_summary = self.complexity_repo.get_summary(project_id)

        # Get counts
        summary = self.project_repo.get_summary(project_id)

        return ProjectDetail(
            id=project.id,
            name=project.name,
            root_path=project.root_path,
            source_type=project.source_type,
            source_url=project.source_url,
            created_at=project.created_at,
            updated_at=project.updated_at,
            zip_uploaded_at=project.zip_uploaded_at,
            first_file_created=project.first_file_created,
            first_commit_date=project.first_commit_date,
            project_started_at=project.project_started_at,
            file_count=summary["file_count"] if summary else 0,
            language_count=summary["language_count"] if summary else 0,
            framework_count=summary["framework_count"] if summary else 0,
            contributor_count=summary["contributor_count"] if summary else 0,
            skill_count=summary["skill_count"] if summary else 0,
            languages=languages,
            frameworks=frameworks,
            total_lines_of_code=total_loc,
            avg_complexity=complexity_summary.get("avg_complexity", 0.0),
            max_complexity=complexity_summary.get("max_complexity", 0),
        )

    def get_project_by_name(self, name: str) -> Optional[ProjectDetail]:
        """
        Get project by name.

        Args:
            name: Name of the project

        Returns:
            ProjectDetail or None if not found
        """
        project = self.project_repo.get_by_name(name)
        if not project:
            return None
        return self.get_project(project.id)

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project and all associated data.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if deleted, False if not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return False

        logger.info(f"Deleting project {project_id}: {project.name}")
        return self.project_repo.delete(project_id)

    def project_exists(self, project_id: int) -> bool:
        """Check if a project exists."""
        return self.project_repo.get(project_id) is not None
