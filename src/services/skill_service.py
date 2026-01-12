"""Skill service for skill operations."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.models.schemas.skill import (
    ProjectSkillsResponse,
    SkillSchema,
    SkillTimelineResponse,
    SkillTimelineEntry,
)
from src.repositories.project_repository import ProjectRepository
from src.repositories.skill_repository import SkillRepository

logger = logging.getLogger(__name__)


class SkillService:
    """Service for skill operations."""

    def __init__(self, db: Session):
        """Initialize skill service with database session."""
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.skill_repo = SkillRepository(db)

    def get_project_skills(self, project_id: int) -> Optional[ProjectSkillsResponse]:
        """
        Get all skills for a project grouped by category.

        Args:
            project_id: ID of the project

        Returns:
            ProjectSkillsResponse or None if project not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return None

        # Get languages and frameworks
        languages = self.project_repo.get_languages(project_id)
        frameworks = self.project_repo.get_frameworks(project_id)

        # Get skills grouped by category
        skills_grouped = self.skill_repo.get_grouped_by_category(project_id)

        skills_by_category = {}
        total_skills = 0

        for category, skills in skills_grouped.items():
            skill_schemas = []
            for skill in skills:
                skill_schemas.append(SkillSchema(
                    name=skill.skill,
                    category=skill.category,
                    frequency=skill.frequency,
                ))
                total_skills += 1
            skills_by_category[category] = skill_schemas

        return ProjectSkillsResponse(
            project_id=project_id,
            project_name=project.name,
            languages=languages,
            frameworks=frameworks,
            skills_by_category=skills_by_category,
            total_skills=total_skills,
            total_categories=len(skills_by_category),
        )

    def get_skill_timeline(
        self,
        project_id: int,
        skill: Optional[str] = None,
    ) -> Optional[SkillTimelineResponse]:
        """
        Get skill timeline for a project.

        Args:
            project_id: ID of the project
            skill: Optional specific skill to filter

        Returns:
            SkillTimelineResponse or None if project not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return None

        timeline_entries = self.skill_repo.get_timeline(project_id, skill)

        timeline = []
        for entry in timeline_entries:
            timeline.append(SkillTimelineEntry(
                skill=entry.skill,
                date=entry.date.isoformat() if entry.date else "",
                count=entry.count,
            ))

        return SkillTimelineResponse(
            project_id=project_id,
            timeline=timeline,
        )

    def get_skill_categories(self, project_id: int) -> list:
        """Get all skill categories for a project."""
        return self.skill_repo.get_categories(project_id)
