"""Skill repository for database operations."""

from datetime import date
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
        """
        Create multiple skills efficiently.

        Supports source tracking columns:
        - source: "language", "framework", "library", "tool", "contextual", "file_type"
        - source_id: ID of the related entity
        - cross_validation_boost: Confidence boost from cross-validation
        """
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
                    "source": data.get("source"),
                    "source_id": data.get("source_id"),
                    "cross_validation_boost": data.get("cross_validation_boost"),
                }

        skills = []
        for data in skill_map.values():
            skill = ProjectSkill(
                project_id=data["project_id"],
                skill=data["skill"],
                category=data["category"],
                frequency=data["frequency"],
                source=data.get("source"),
                source_id=data.get("source_id"),
                cross_validation_boost=data.get("cross_validation_boost"),
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
        """Get skill timeline for a project (case-insensitive skill filter)."""
        stmt = select(ProjectSkillTimeline).where(ProjectSkillTimeline.project_id == project_id)
        if skill:
            stmt = stmt.where(func.lower(ProjectSkillTimeline.skill) == func.lower(skill))
        stmt = stmt.order_by(ProjectSkillTimeline.date)
        return list(self.db.scalars(stmt).all())

    def create_timeline_entry(
        self,
        project_id: int,
        skill: str,
        skill_date: date,
        count: int = 1,
    ) -> ProjectSkillTimeline:
        """
        Create or update a timeline entry for a skill on a specific date.

        Args:
            project_id: Project ID
            skill: Skill name
            skill_date: Date when skill was used
            count: Number of occurrences

        Returns:
            The created or updated timeline entry
        """
        # Check if entry already exists
        existing = self.db.scalar(
            select(ProjectSkillTimeline)
            .where(ProjectSkillTimeline.project_id == project_id)
            .where(func.lower(ProjectSkillTimeline.skill) == func.lower(skill))
            .where(ProjectSkillTimeline.date == skill_date)
        )
        if existing:
            existing.count += count
            self.db.commit()
            self.db.refresh(existing)
            return existing

        entry = ProjectSkillTimeline(
            project_id=project_id,
            skill=skill,
            date=skill_date,
            count=count,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def create_timeline_bulk(self, timeline_data: List[dict]) -> List[ProjectSkillTimeline]:
        """
        Create multiple timeline entries efficiently.

        Args:
            timeline_data: List of dicts with project_id, skill, date, count

        Returns:
            List of created timeline entries
        """
        # Aggregate by (project_id, skill_lower, date) to handle duplicates
        # but preserve original skill name casing
        aggregated: Dict[tuple, tuple] = {}  # key -> (original_skill, count)
        for data in timeline_data:
            skill = data["skill"]
            key = (data["project_id"], skill.lower(), data["date"])
            if key in aggregated:
                orig_skill, existing_count = aggregated[key]
                aggregated[key] = (orig_skill, existing_count + data.get("count", 1))
            else:
                aggregated[key] = (skill, data.get("count", 1))

        entries = []
        for (project_id, _, skill_date), (skill, count) in aggregated.items():
            entry = ProjectSkillTimeline(
                project_id=project_id,
                skill=skill,  # Original casing preserved
                date=skill_date,
                count=count,
            )
            entries.append(entry)

        if entries:
            self.db.add_all(entries)
            self.db.commit()
            for entry in entries:
                self.db.refresh(entry)

        return entries

    # Source-based skill queries for complementary detection system
    def get_skills_by_source(self, project_id: int, source: str) -> List[ProjectSkill]:
        """
        Get skills filtered by source type.

        Args:
            project_id: Project ID
            source: Source type (language, framework, library, tool, contextual, file_type)

        Returns:
            List of ProjectSkill objects filtered by source
        """
        stmt = (
            select(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .where(ProjectSkill.source == source)
            .order_by(ProjectSkill.frequency.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_skills_with_sources(self, project_id: int) -> List[ProjectSkill]:
        """
        Get all skills with source information.

        Args:
            project_id: Project ID

        Returns:
            List of ProjectSkill objects with source information
        """
        stmt = (
            select(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .order_by(ProjectSkill.source, ProjectSkill.category, ProjectSkill.frequency.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_skill_source_breakdown(self, project_id: int) -> Dict[str, List[ProjectSkill]]:
        """
        Group skills by source type.

        Args:
            project_id: Project ID

        Returns:
            Dictionary mapping source types to lists of skills
        """
        skills = self.get_skills_with_sources(project_id)
        breakdown: Dict[str, List[ProjectSkill]] = {
            "language": [],
            "framework": [],
            "library": [],
            "tool": [],
            "contextual": [],
            "file_type": [],
            "unknown": [],
        }

        for skill in skills:
            source = skill.source or "unknown"
            if source in breakdown:
                breakdown[source].append(skill)
            else:
                breakdown["unknown"].append(skill)

        return breakdown

    def count_by_source(self, project_id: int) -> Dict[str, int]:
        """
        Count skills by source type for a project.

        Args:
            project_id: Project ID

        Returns:
            Dictionary mapping source types to counts
        """
        stmt = (
            select(ProjectSkill.source, func.count(ProjectSkill.id))
            .where(ProjectSkill.project_id == project_id)
            .group_by(ProjectSkill.source)
        )
        results = self.db.execute(stmt).all()
        return {source or "unknown": count for source, count in results}
