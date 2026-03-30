"""Skill repository for database operations."""

from datetime import date, datetime
import json
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.orm.project import ProjectAnalysisSummary
from src.models.orm.skill import (
    ProjectSkill,
    ProjectSkillTimeline,
    Skill,
    SkillOccurrence,
)
from src.repositories.base import BaseRepository


class SkillRepository(BaseRepository[ProjectSkill]):
    """Repository for skill operations."""

    def __init__(self, db: Session):
        """Initialize skill repository."""
        super().__init__(ProjectSkill, db)

    def get_by_project(self, project_id: int) -> List[ProjectSkill]:
        """Get all skills for a project with skill details joined."""
        stmt = (
            select(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .join(Skill)
            .order_by(Skill.category, ProjectSkill.frequency.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_category(self, project_id: int, category: str) -> List[ProjectSkill]:
        """Get skills by category for a project."""
        stmt = (
            select(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .join(Skill)
            .where(Skill.category == category)
            .order_by(ProjectSkill.frequency.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_grouped_by_category(self, project_id: int) -> Dict[str, List[ProjectSkill]]:
        """Get skills grouped by category."""
        skills = self.get_by_project(project_id)
        grouped = {}
        for project_skill in skills:
            category = project_skill.skill.category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(project_skill)
        return grouped

    def get_categories(self, project_id: int) -> List[str]:
        """Get all unique categories for a project."""
        stmt = (
            select(Skill.category)
            .join(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .distinct()
        )
        return list(self.db.scalars(stmt).all())

    def create_skill(
        self,
        project_id: int,
        skill_name: str,
        category: str,
        frequency: int = 1,
        source: Optional[str] = None,
    ) -> ProjectSkill:
        """
        Create a new project skill, using skill lookup table.

        Args:
            project_id: Project ID
            skill_name: Name of the skill
            category: Category of the skill
            frequency: Occurrence count
            source: Detection source

        Returns:
            ProjectSkill instance
        """
        # Get or create skill in lookup table
        skill = self.db.scalar(
            select(Skill)
            .where(Skill.name == skill_name)
            .where(Skill.category == category)
        )
        if not skill:
            skill = Skill(name=skill_name, category=category)
            self.db.add(skill)
            self.db.flush()

        # Check if project skill already exists
        existing = self.db.scalar(
            select(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .where(ProjectSkill.skill_id == skill.id)
        )
        if existing:
            existing.frequency += frequency
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create project skill
        project_skill = ProjectSkill(
            project_id=project_id,
            skill_id=skill.id,
            frequency=frequency,
            source=source,
        )
        return self.create(project_skill)

    def create_skills_bulk(self, skills_data: List[dict]) -> List[ProjectSkill]:
        """
        Create multiple skills efficiently using lookup table.

        Args:
            skills_data: List of dicts with keys: project_id, skill, category, frequency, source

        Returns:
            List of created ProjectSkill instances
        """
        from sqlalchemy.exc import IntegrityError

        # First, get or create all unique skills in lookup table
        skill_lookup = {}  # Key: (skill_name, category) -> Skill
        for data in skills_data:
            key = (data["skill"], data["category"])
            if key not in skill_lookup:
                skill = self.db.scalar(
                    select(Skill)
                    .where(Skill.name == data["skill"])
                    .where(Skill.category == data["category"])
                )
                if not skill:
                    try:
                        skill = Skill(name=data["skill"], category=data["category"])
                        self.db.add(skill)
                        self.db.flush()
                    except IntegrityError:
                        # Skill already exists (race condition or duplicate in batch)
                        # Retry the query
                        self.db.rollback()
                        skill = self.db.scalar(
                            select(Skill)
                            .where(Skill.name == data["skill"])
                            .where(Skill.category == data["category"])
                        )
                        if not skill:
                            raise  # Re-raise if still not found

                skill_lookup[key] = skill

        # Group by project_id, skill_id to handle duplicates
        project_skill_map = {}
        for data in skills_data:
            skill = skill_lookup[(data["skill"], data["category"])]
            key = (data["project_id"], skill.id)

            if key in project_skill_map:
                project_skill_map[key]["frequency"] += data.get("frequency", 1)
            else:
                project_skill_map[key] = {
                    "project_id": data["project_id"],
                    "skill_id": skill.id,
                    "frequency": data.get("frequency", 1),
                    "source": data.get("source"),
                }

        # Create project skills
        project_skills = []
        for data in project_skill_map.values():
            project_skill = ProjectSkill(
                project_id=data["project_id"],
                skill_id=data["skill_id"],
                frequency=data["frequency"],
                source=data.get("source"),
            )
            project_skills.append(project_skill)

        return self.create_many(project_skills)

    def count_by_project(self, project_id: int) -> int:
        """Count skills in a project."""
        stmt = select(func.count(ProjectSkill.id)).where(ProjectSkill.project_id == project_id)
        return self.db.scalar(stmt) or 0

    # Skill Occurrence operations
    def create_occurrence(
        self,
        project_id: int,
        skill_name: str,
        file_path: str,
        evidence_type: str,
        evidence_value: str,
        first_seen_at: datetime,
        date_source: str,
    ) -> SkillOccurrence:
        """
        Create a single skill occurrence row.

        Args:
            project_id: Project ID
            skill_name: Name of the detected skill
            file_path: File where the skill evidence was found
            evidence_type: Type of evidence (language, framework, library, tool, skill)
            evidence_value: Raw detected value
            first_seen_at: Resolved best date for this file evidence
            date_source: Source of resolved date (git_commit, file_metadata, upload_fallback)

        Returns:
            Created SkillOccurrence instance
        """
        occurrence = SkillOccurrence(
            project_id=project_id,
            skill_name=skill_name,
            file_path=file_path,
            evidence_type=evidence_type,
            evidence_value=evidence_value,
            first_seen_at=first_seen_at,
            date_source=date_source,
        )
        self.db.add(occurrence)
        self.db.flush()
        return occurrence

    def create_occurrences_bulk(self, occurrences_data: List[dict]) -> List[SkillOccurrence]:
        """
        Create multiple skill occurrence rows efficiently.

        Args:
            occurrences_data: List of dicts with keys:
                project_id, skill_name, file_path, evidence_type,
                evidence_value, first_seen_at, date_source

        Returns:
            List of created SkillOccurrence instances
        """
        occurrences = [
            SkillOccurrence(
                project_id=data["project_id"],
                skill_name=data["skill_name"],
                file_path=data["file_path"],
                evidence_type=data["evidence_type"],
                evidence_value=data["evidence_value"],
                first_seen_at=data["first_seen_at"],
                date_source=data["date_source"],
            )
            for data in occurrences_data
        ]

        if occurrences:
            self.db.add_all(occurrences)
            self.db.flush()

        return occurrences

    def delete_occurrences_by_project(self, project_id: int) -> int:
        """
        Delete all skill occurrences for a project.

        Args:
            project_id: Project ID

        Returns:
            Number of deleted rows
        """
        rows = self.db.query(SkillOccurrence).filter(
            SkillOccurrence.project_id == project_id
        )
        deleted_count = rows.count()
        rows.delete(synchronize_session=False)
        self.db.flush()
        return deleted_count

    def get_occurrences_by_project(self, project_id: int) -> List[SkillOccurrence]:
        """
        Get all skill occurrences for a project ordered chronologically.

        Args:
            project_id: Project ID

        Returns:
            List of SkillOccurrence rows
        """
        stmt = (
            select(SkillOccurrence)
            .where(SkillOccurrence.project_id == project_id)
            .order_by(SkillOccurrence.first_seen_at.asc(), SkillOccurrence.skill_name.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_timeline_from_occurrences(
        self,
        project_id: int,
        skill: Optional[str] = None,
    ):
        """
        Aggregate skill timeline directly from skill_occurrences.

        For each skill:
        - date = earliest first_seen_at
        - count = total number of occurrence rows for that skill

        Args:
            project_id: Project ID
            skill: Optional case-insensitive skill filter

        Returns:
            Aggregated SQLAlchemy result rows with fields: skill, date, count
        """
        stmt = (
            select(
                SkillOccurrence.skill_name.label("skill"),
                func.min(SkillOccurrence.first_seen_at).label("date"),
                func.count(SkillOccurrence.id).label("count"),
            )
            .where(SkillOccurrence.project_id == project_id)
            .group_by(SkillOccurrence.skill_name)
            .order_by(func.min(SkillOccurrence.first_seen_at).asc())
        )

        if skill:
            stmt = stmt.where(func.lower(SkillOccurrence.skill_name) == func.lower(skill))

        return self.db.execute(stmt).all()

    # Skill Summary operations
    def get_summary(self, project_id: int) -> Optional[ProjectAnalysisSummary]:
        """Get analysis summary for a project."""
        stmt = select(ProjectAnalysisSummary).where(ProjectAnalysisSummary.project_id == project_id)
        return self.db.scalar(stmt)

    def create_summary(
        self,
        project_id: int,
        total_files_processed: int = 0,
        total_files_analyzed: int = 0,
        total_files_skipped: int = 0,
        analysis_duration_seconds: float = 0.0,
        stage_durations: Optional[Dict[str, float]] = None,
    ) -> ProjectAnalysisSummary:
        """Create or update analysis summary, including timing metadata."""
        existing = self.get_summary(project_id)
        if existing:
            existing.total_files_processed = total_files_processed
            existing.total_files_analyzed = total_files_analyzed
            existing.total_files_skipped = total_files_skipped
            existing.analysis_duration_seconds = analysis_duration_seconds
            if stage_durations is not None:
                existing.analysis_stage_durations = json.dumps(stage_durations)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        summary = ProjectAnalysisSummary(
            project_id=project_id,
            total_files_processed=total_files_processed,
            total_files_analyzed=total_files_analyzed,
            total_files_skipped=total_files_skipped,
            analysis_duration_seconds=analysis_duration_seconds,
            analysis_stage_durations=json.dumps(stage_durations) if stage_durations else None,
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
            .join(Skill)
            .where(ProjectSkill.project_id == project_id)
            .order_by(ProjectSkill.source, Skill.category, ProjectSkill.frequency.desc())
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