"""Skill service for skill operations."""

import logging
from typing import Any, List, Optional

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
        Get skill timeline for a project from skill occurrences.

        Args:
            project_id: ID of the project
            skill: Optional specific skill to filter

        Returns:
            SkillTimelineResponse or None if project not found
        """
        project = self.project_repo.get(project_id)
        if not project:
            return None

        timeline_rows = self.skill_repo.get_timeline_from_occurrences(project_id, skill)

        timeline = [
            SkillTimelineEntry(
                skill=row.skill,
                date=row.date.isoformat() if row.date else "",
                count=row.count,
            )
            for row in timeline_rows
        ]

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

        def _to_schema(project_skill: Any) -> SkillSchema:
            # Normalize ORM object into the API schema using the related Skill entity
            skill = project_skill.skill
            return SkillSchema(
                name=skill.name if skill else "",
                category=skill.category if skill else "",
                frequency=project_skill.frequency,
                source=project_skill.source,
            )

        def _to_schemas(skills) -> List[SkillSchema]:
            return [_to_schema(s) for s in skills]

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

        def _to_schema(project_skill: Any) -> SkillSchema:
            skill = project_skill.skill
            return SkillSchema(
                name=skill.name if skill else "",
                category=skill.category if skill else "",
                frequency=project_skill.frequency,
                source=project_skill.source,
            )

        skill_schemas = [_to_schema(s) for s in skills]

        return SkillsBySourceResponse(
            project_id=project_id,
            source=source,
            skills=skill_schemas,
            total=len(skill_schemas),
        )
    
    def build_skill_timeline(
        self,
        project_id: int,
        skill: Optional[str] = None,
    ) -> Optional[SkillTimelineResponse]:
        project = self.project_repo.get(project_id)
        if not project:
            return None

        logger.info("[TIMELINE BUILD] starting project_id=%s", project_id)

        from src.services.analysis_service import AnalysisService

        analysis_service = AnalysisService(self.db)
        analysis_service.rebuild_skill_occurrences_for_project(project_id)

        result = self.get_skill_timeline(project_id, skill)

        logger.info(
            "[TIMELINE BUILD] returning project_id=%s entries=%d",
            project_id,
            len(result.timeline) if result else -1,
        )

        return result