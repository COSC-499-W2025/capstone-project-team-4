"""Skill repository for database operations."""

from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.orm.skill import ProjectSkill, ProjectSkillSummary, ProjectSkillTimeline, Skill
from src.repositories.base import BaseRepository


class SkillRepository(BaseRepository[ProjectSkill]):
    """Repository for skill operations."""

    def __init__(self, db: Session):
        """Initialize skill repository."""
        super().__init__(ProjectSkill, db)

    def get_by_project(self, project_id: int) -> List[ProjectSkill]:
        """Get all skills for a project."""
        stmt = (
            select(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .order_by(ProjectSkill.category, ProjectSkill.frequency.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_category(self, project_id: int, category: str) -> List[ProjectSkill]:
        """Get skills by category for a project."""
        stmt = (
            select(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .where(ProjectSkill.category == category)
            .order_by(ProjectSkill.frequency.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_grouped_by_category(self, project_id: int) -> Dict[str, List[ProjectSkill]]:
        """Get skills grouped by category."""
        skills = self.get_by_project(project_id)
        grouped = {}
        for skill in skills:
            if skill.category not in grouped:
                grouped[skill.category] = []
            grouped[skill.category].append(skill)
        return grouped

    def get_categories(self, project_id: int) -> List[str]:
        """Get all unique categories for a project."""
        stmt = (
            select(ProjectSkill.category)
            .where(ProjectSkill.project_id == project_id)
            .distinct()
        )
        return list(self.db.scalars(stmt).all())

    def create_skill(
        self,
        project_id: int,
        skill: str,
        category: str,
        frequency: int = 1,
    ) -> ProjectSkill:
        """Create a new project skill."""
        # Check if skill already exists for this project
        existing = self.db.scalar(
            select(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .where(ProjectSkill.skill == skill)
            .where(ProjectSkill.category == category)
        )
        if existing:
            existing.frequency += frequency
            self.db.commit()
            self.db.refresh(existing)
            return existing

        project_skill = ProjectSkill(
            project_id=project_id,
            skill=skill,
            category=category,
            frequency=frequency,
        )
        return self.create(project_skill)

    def create_skills_bulk(self, skills_data: List[dict]) -> List[ProjectSkill]:
        """Create multiple skills efficiently."""
        # Group by project_id, skill, category to handle duplicates
        skill_map = {}
        for data in skills_data:
            key = (data["project_id"], data["skill"], data["category"])
            if key in skill_map:
                skill_map[key]["frequency"] += data.get("frequency", 1)
            else:
                skill_map[key] = {
                    "project_id": data["project_id"],
                    "skill": data["skill"],
                    "category": data["category"],
                    "frequency": data.get("frequency", 1),
                }

        skills = []
        for data in skill_map.values():
            skill = ProjectSkill(
                project_id=data["project_id"],
                skill=data["skill"],
                category=data["category"],
                frequency=data["frequency"],
            )
            skills.append(skill)
        return self.create_many(skills)

    def count_by_project(self, project_id: int) -> int:
        """Count skills in a project."""
        stmt = select(func.count(ProjectSkill.id)).where(ProjectSkill.project_id == project_id)
        return self.db.scalar(stmt) or 0

    # Skill Summary operations
    def get_summary(self, project_id: int) -> Optional[ProjectSkillSummary]:
        """Get skill summary for a project."""
        stmt = select(ProjectSkillSummary).where(ProjectSkillSummary.project_id == project_id)
        return self.db.scalar(stmt)

    def create_summary(
        self,
        project_id: int,
        total_files: int = 0,
        files_analyzed: int = 0,
        files_skipped: int = 0,
    ) -> ProjectSkillSummary:
        """Create or update skill summary."""
        existing = self.get_summary(project_id)
        if existing:
            existing.total_files = total_files
            existing.files_analyzed = files_analyzed
            existing.files_skipped = files_skipped
            self.db.commit()
            self.db.refresh(existing)
            return existing

        summary = ProjectSkillSummary(
            project_id=project_id,
            total_files=total_files,
            files_analyzed=files_analyzed,
            files_skipped=files_skipped,
        )
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary

    # Skill Timeline operations
    def get_timeline(self, project_id: int, skill: Optional[str] = None) -> List[ProjectSkillTimeline]:
        """Get skill timeline for a project."""
        stmt = select(ProjectSkillTimeline).where(ProjectSkillTimeline.project_id == project_id)
        if skill:
            stmt = stmt.where(ProjectSkillTimeline.skill == skill)
        stmt = stmt.order_by(ProjectSkillTimeline.date)
        return list(self.db.scalars(stmt).all())
