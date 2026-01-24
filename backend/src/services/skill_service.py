"""Skill service for skill operations."""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.schemas.skill import (
    ProjectSkillsResponse,
    SkillSchema,
    SkillSourceBreakdown,
    SkillSourceResponse,
    SkillsBySourceResponse,
    SkillTimelineEntry,
    SkillTimelineResponse,
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

        project_skills = self.skill_repo.get_by_project(project_id)
        skill_names = [ps.skill.name for ps in project_skills]

        return ProjectSkillsResponse(
            project_id=project_id,
            project_name=project.name,
            skills=skill_names,
            total_skills=len(project_skills),
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

        # Fallback: if no timeline data exists, synthesize a single snapshot from current skills
        if not timeline:
            skills = self.skill_repo.get_by_project(project_id)
            if skill:
                skills = [s for s in skills if s.skill.lower() == skill.lower()]
            if skills:
                snapshot_date = (project.created_at.date() if project.created_at else None)
                snapshot_date_str = snapshot_date.isoformat() if snapshot_date else ""
                for s in skills:
                    timeline.append(SkillTimelineEntry(
                        skill=s.skill,
                        date=snapshot_date_str,
                        count=s.frequency,
                    ))

        return SkillTimelineResponse(
            project_id=project_id,
            timeline=timeline,
        )

    def get_skill_categories(self, project_id: int) -> list:
        """Get all skill categories for a project."""
        return self.skill_repo.get_categories(project_id)

    def get_skill_sources(self, project_id: int) -> SkillSourceResponse:
        """
        Get skills grouped by their detection source.

        Args:
            project_id: ID of the project

        Returns:
            SkillSourceResponse with skills grouped by source
        """
        breakdown = self.skill_repo.get_skill_source_breakdown(project_id)
        source_counts = self.skill_repo.count_by_source(project_id)

        def _to_schemas(skills) -> List[SkillSchema]:
            return [
                SkillSchema(
                    name=s.skill,
                    category=s.category,
                    frequency=s.frequency,
                    source=s.source,
                )
                for s in skills
            ]

        return SkillSourceResponse(
            project_id=project_id,
            breakdown=SkillSourceBreakdown(
                from_languages=_to_schemas(breakdown.get("language", [])),
                from_frameworks=_to_schemas(breakdown.get("framework", [])),
                from_libraries=_to_schemas(breakdown.get("library", [])),
                from_tools=_to_schemas(breakdown.get("tool", [])),
                contextual=_to_schemas(breakdown.get("contextual", [])),
                from_file_types=_to_schemas(breakdown.get("file_type", [])),
            ),
            source_counts=source_counts,
        )

    def get_skills_by_source(
        self,
        project_id: int,
        source: str,
    ) -> SkillsBySourceResponse:
        """
        Get skills filtered by a specific source type.

        Args:
            project_id: ID of the project
            source: Source type to filter by

        Returns:
            SkillsBySourceResponse with filtered skills
        """
        skills = self.skill_repo.get_skills_by_source(project_id, source)

        skill_schemas = [
            SkillSchema(
                name=s.skill,
                category=s.category,
                frequency=s.frequency,
                source=s.source,
            )
            for s in skills
        ]

        return SkillsBySourceResponse(
            project_id=project_id,
            source=source,
            skills=skill_schemas,
            total=len(skill_schemas),
        )
