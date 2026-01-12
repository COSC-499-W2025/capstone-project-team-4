"""Resume service for resume item operations."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.schemas.resume import (
    ResumeItemSchema,
    ProjectResumeResponse,
)
from src.repositories.project_repository import ProjectRepository
from src.repositories.resume_repository import ResumeRepository
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.complexity_repository import ComplexityRepository
from src.repositories.skill_repository import SkillRepository
from src.repositories.file_repository import FileRepository

# Import resume generator
from src.core.resume_item_generator import generate_resume_item

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for resume item operations."""

    def __init__(self, db: Session):
        """Initialize resume service with database session."""
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.contributor_repo = ContributorRepository(db)
        self.complexity_repo = ComplexityRepository(db)
        self.skill_repo = SkillRepository(db)
        self.file_repo = FileRepository(db)

    def get_project_resume(self, project_id: int) -> Optional[ProjectResumeResponse]:
        """
        Get resume items for a project.

        Args:
            project_id: ID of the project

        Returns:
            ProjectResumeResponse or None if project not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return None

        resume_items = self.resume_repo.get_by_project(project_id)

        items = []
        for item in resume_items:
            items.append(ResumeItemSchema(
                id=item.id,
                project_id=item.project_id,
                title=item.title,
                highlights=item.highlights or [],
                created_at=item.created_at,
            ))

        return ProjectResumeResponse(
            project_id=project_id,
            project_name=project.name,
            resume_items=items,
        )

    def get_latest_resume_item(self, project_id: int) -> Optional[ResumeItemSchema]:
        """
        Get the most recent resume item for a project.

        Args:
            project_id: ID of the project

        Returns:
            ResumeItemSchema or None if not found
        """
        item = self.resume_repo.get_latest(project_id)
        if not item:
            return None

        return ResumeItemSchema(
            id=item.id,
            project_id=item.project_id,
            title=item.title,
            highlights=item.highlights or [],
            created_at=item.created_at,
        )

    def regenerate_resume(self, project_id: int) -> Optional[ResumeItemSchema]:
        """
        Regenerate resume item for a project based on current analysis data.

        Args:
            project_id: ID of the project

        Returns:
            New ResumeItemSchema or None if project not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return None

        # Gather data for resume generation
        contributors = self._get_contributors_data(project_id)
        project_stats = self._get_project_stats(project_id)
        skill_categories = self._get_skill_categories(project_id)
        languages = self.project_repo.get_languages(project_id)
        frameworks = self.project_repo.get_frameworks(project_id)
        complexity_dict = self._get_complexity_dict(project_id)

        # Generate new resume item
        resume_data = generate_resume_item(
            project_name=project.name,
            contributors=contributors,
            project_stats=project_stats,
            skill_categories=skill_categories,
            languages=languages,
            frameworks=frameworks,
            complexity_dict=complexity_dict,
        )

        # Save to database
        resume_item = self.resume_repo.create_resume_item(
            project_id=project_id,
            title=resume_data.get("title", ""),
            highlights=resume_data.get("highlights", []),
        )

        return ResumeItemSchema(
            id=resume_item.id,
            project_id=resume_item.project_id,
            title=resume_item.title,
            highlights=resume_item.highlights or [],
            created_at=resume_item.created_at,
        )

    def update_resume_item(
        self,
        resume_id: int,
        title: Optional[str] = None,
        highlights: Optional[List[str]] = None,
    ) -> Optional[ResumeItemSchema]:
        """
        Update an existing resume item.

        Args:
            resume_id: ID of the resume item
            title: New title (optional)
            highlights: New highlights (optional)

        Returns:
            Updated ResumeItemSchema or None if not found
        """
        item = self.resume_repo.update_resume_item(
            resume_id=resume_id,
            title=title,
            highlights=highlights,
        )

        if not item:
            return None

        return ResumeItemSchema(
            id=item.id,
            project_id=item.project_id,
            title=item.title,
            highlights=item.highlights or [],
            created_at=item.created_at,
        )

    def _get_contributors_data(self, project_id: int) -> List[dict]:
        """Get contributors data in format expected by resume generator."""
        contributors = self.contributor_repo.get_by_project(project_id)
        result = []
        for c in contributors:
            contrib_with_files = self.contributor_repo.get_with_files(c.id)
            files_modified = {}
            if contrib_with_files:
                for f in contrib_with_files.files_modified:
                    files_modified[f.filename] = f.modifications

            result.append({
                "name": c.name,
                "email": c.email,
                "commits": c.commits,
                "percent": c.percent,
                "total_lines_added": c.total_lines_added,
                "total_lines_deleted": c.total_lines_deleted,
                "files_modified": files_modified,
            })
        return result

    def _get_project_stats(self, project_id: int) -> dict:
        """Get project stats for resume generator."""
        file_count = self.file_repo.count_by_project(project_id)
        total_loc = self.project_repo.get_total_lines_of_code(project_id)

        return {
            "total_files": file_count,
            "total_lines": total_loc,
        }

    def _get_skill_categories(self, project_id: int) -> dict:
        """Get skill categories for resume generator."""
        skills_grouped = self.skill_repo.get_grouped_by_category(project_id)
        result = {}
        for category, skills in skills_grouped.items():
            result[category] = [s.skill for s in skills]
        return result

    def _get_complexity_dict(self, project_id: int) -> dict:
        """Get complexity dict for resume generator."""
        summary = self.complexity_repo.get_summary(project_id)
        complexities = self.complexity_repo.get_by_project(project_id, limit=1000)

        functions = []
        for c in complexities:
            functions.append({
                "file_path": c.file_path,
                "function_name": c.function_name,
                "cyclomatic_complexity": c.cyclomatic_complexity,
                "start_line": c.start_line,
                "end_line": c.end_line,
            })

        return {
            "functions": functions,
            "summary": summary,
        }
