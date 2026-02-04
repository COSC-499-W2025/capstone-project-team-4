"""Service for managing snapshot comparisons."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.models.orm import Project, SnapshotComparison
from src.models.schemas.test_data import SnapshotMetrics, MetricComparison, SnapshotComparison as SnapshotComparisonSchema
from src.services.project_service import ProjectService
from src.repositories.project_repository import ProjectRepository
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.complexity_repository import ComplexityRepository
from src.repositories.skill_repository import SkillRepository

logger = logging.getLogger(__name__)


class SnapshotService:
    """Handles snapshot comparison operations."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.project_service = ProjectService(db)
        self.project_repo = ProjectRepository(db)
        self.contributor_repo = ContributorRepository(db)
        self.complexity_repo = ComplexityRepository(db)
        self.skill_repo = SkillRepository(db)

    def create_comparison(
        self,
        snapshot1_id: int,
        snapshot2_id: int
    ) -> SnapshotComparison:
        """
        Create and persist a snapshot comparison.

        Args:
            snapshot1_id: ID of first snapshot
            snapshot2_id: ID of second snapshot

        Returns:
            Created SnapshotComparison record

        Raises:
            ValueError: If projects don't exist
        """
        # Get projects from repository (ORM objects)
        project1 = self.project_repo.get(snapshot1_id)
        project2 = self.project_repo.get(snapshot2_id)

        if not project1:
            raise ValueError(f"Project 1 not found: ID {snapshot1_id}")
        if not project2:
            raise ValueError(f"Project 2 not found: ID {snapshot2_id}")

        # Convert to metrics
        metrics1 = self._convert_to_snapshot_metrics(project1)
        metrics2 = self._convert_to_snapshot_metrics(project2)

        # Calculate comparisons
        comparison_data = self._calculate_comparisons(metrics1, metrics2)

        # Generate summary
        summary = self._generate_summary(metrics1, metrics2, comparison_data)

        # Create database record
        comparison = SnapshotComparison(
            snapshot1_id=snapshot1_id,
            snapshot2_id=snapshot2_id,
            summary=summary,
            metric_changes=comparison_data["metric_changes"],
            new_languages=comparison_data["new_languages"],
            new_frameworks=comparison_data["new_frameworks"],
            new_libraries=comparison_data["new_libraries"],
            new_contributors=comparison_data["new_contributors"],
        )

        self.db.add(comparison)
        self.db.commit()
        self.db.refresh(comparison)

        logger.info(f"Created comparison between projects {snapshot1_id} and {snapshot2_id}")
        return comparison

    def get_comparison(
        self,
        snapshot1_id: int,
        snapshot2_id: int
    ) -> Optional[SnapshotComparison]:
        """
        Get existing comparison between two snapshots.

        Args:
            snapshot1_id: ID of first snapshot
            snapshot2_id: ID of second snapshot

        Returns:
            SnapshotComparison record if exists, None otherwise
        """
        return self.db.query(SnapshotComparison).filter(
            SnapshotComparison.snapshot1_id == snapshot1_id,
            SnapshotComparison.snapshot2_id == snapshot2_id
        ).first()

    def get_or_create_comparison(
        self,
        snapshot1_id: int,
        snapshot2_id: int
    ) -> SnapshotComparison:
        """
        Get existing comparison or create new one.

        Args:
            snapshot1_id: ID of first snapshot
            snapshot2_id: ID of second snapshot

        Returns:
            SnapshotComparison record
        """
        existing = self.get_comparison(snapshot1_id, snapshot2_id)
        if existing:
            logger.info(f"Found existing comparison for {snapshot1_id} and {snapshot2_id}")
            return existing

        return self.create_comparison(snapshot1_id, snapshot2_id)

    def get_comparison_schema(
        self,
        snapshot1_id: int,
        snapshot2_id: int
    ) -> SnapshotComparisonSchema:
        """
        Get comparison as Pydantic schema for API response.

        Args:
            snapshot1_id: ID of first snapshot
            snapshot2_id: ID of second snapshot

        Returns:
            SnapshotComparisonSchema
        """
        # Get or create comparison
        comparison = self.get_or_create_comparison(snapshot1_id, snapshot2_id)

        # Get projects from repository (ORM objects for metrics)
        project1 = self.project_repo.get(snapshot1_id)
        project2 = self.project_repo.get(snapshot2_id)

        metrics1 = self._convert_to_snapshot_metrics(project1)
        metrics2 = self._convert_to_snapshot_metrics(project2)

        # Build response
        metric_changes = comparison.metric_changes

        return SnapshotComparisonSchema(
            snapshot1_name=project1.name,
            snapshot2_name=project2.name,
            summary=comparison.summary,
            contributors=MetricComparison(**metric_changes["contributors"]),
            languages=MetricComparison(**metric_changes["languages"]),
            frameworks=MetricComparison(**metric_changes["frameworks"]),
            libraries=MetricComparison(**metric_changes["libraries"]),
            skills=MetricComparison(**metric_changes["skills"]),
            total_files=MetricComparison(**metric_changes["total_files"]),
            total_loc=MetricComparison(**metric_changes["total_loc"]),
            avg_complexity=MetricComparison(**metric_changes["avg_complexity"]),
            snapshot1_metrics=metrics1,
            snapshot2_metrics=metrics2,
            new_contributors=comparison.new_contributors or [],
            new_languages=comparison.new_languages or [],
            new_frameworks=comparison.new_frameworks or [],
            new_libraries=comparison.new_libraries or [],
        )

    def _convert_to_snapshot_metrics(self, project: Project) -> SnapshotMetrics:
        """Convert Project ORM to SnapshotMetrics."""
        # Get complexity summary
        complexity_summary = self.complexity_repo.get_summary(project.id)

        # Get contributor count
        contributor_count = self.contributor_repo.count_by_project(project.id)

        # Get lists from project repository
        languages = self.project_repo.get_languages(project.id)
        frameworks = self.project_repo.get_frameworks(project.id)
        libraries = self.project_repo.get_libraries(project.id)

        # Get skill count
        skill_count = self.skill_repo.count_by_project(project.id)

        # Get total LOC
        total_loc = self.project_repo.get_total_lines_of_code(project.id)

        return SnapshotMetrics(
            snapshot_name=project.name,
            total_commits=contributor_count,  # Use contributor count as proxy for commits
            contributor_count=contributor_count,
            languages=languages,
            frameworks=frameworks,
            libraries=libraries,
            tools=[],  # Tools would need to be queried separately if needed
            skill_count=skill_count,
            total_files=len(project.files) if project.files else 0,
            total_loc=total_loc,
            avg_complexity=complexity_summary.get("avg_complexity", 0.0),
            first_commit_date=project.first_commit_date.isoformat() if project.first_commit_date else None,
        )

    def _calculate_comparisons(self, metrics1: SnapshotMetrics, metrics2: SnapshotMetrics) -> dict:
        """Calculate metric comparisons and new items."""
        def calc_change(val1, val2):
            """Calculate absolute change and percent change."""
            if isinstance(val1, list):
                val1 = len(val1)
            if isinstance(val2, list):
                val2 = len(val2)

            change = val2 - val1
            percent_change = (change / val1 * 100) if val1 > 0 else (100.0 if val2 > 0 else 0.0)

            return {
                "snapshot1_value": val1 if not isinstance(val1, list) else metrics1.__dict__.get(val1, []),
                "snapshot2_value": val2 if not isinstance(val2, list) else metrics2.__dict__.get(val2, []),
                "change": change,
                "percent_change": round(percent_change, 2)
            }

        # Calculate new items
        new_languages = list(set(metrics2.languages) - set(metrics1.languages))
        new_frameworks = list(set(metrics2.frameworks) - set(metrics1.frameworks))
        new_libraries = list(set(metrics2.libraries) - set(metrics1.libraries))
        new_contributors = []  # Would need contributor names from database

        # Build metric changes
        metric_changes = {
            "contributors": {
                "snapshot1_value": metrics1.contributor_count,
                "snapshot2_value": metrics2.contributor_count,
                "change": metrics2.contributor_count - metrics1.contributor_count,
                "percent_change": round(
                    ((metrics2.contributor_count - metrics1.contributor_count) / metrics1.contributor_count * 100)
                    if metrics1.contributor_count > 0
                    else (100.0 if metrics2.contributor_count > 0 else 0.0),
                    2
                )
            },
            "languages": {
                "snapshot1_value": metrics1.languages,
                "snapshot2_value": metrics2.languages,
                "change": len(metrics2.languages) - len(metrics1.languages),
                "percent_change": round(
                    ((len(metrics2.languages) - len(metrics1.languages)) / len(metrics1.languages) * 100)
                    if len(metrics1.languages) > 0
                    else (100.0 if len(metrics2.languages) > 0 else 0.0),
                    2
                )
            },
            "frameworks": {
                "snapshot1_value": metrics1.frameworks,
                "snapshot2_value": metrics2.frameworks,
                "change": len(metrics2.frameworks) - len(metrics1.frameworks),
                "percent_change": round(
                    ((len(metrics2.frameworks) - len(metrics1.frameworks)) / len(metrics1.frameworks) * 100)
                    if len(metrics1.frameworks) > 0
                    else (100.0 if len(metrics2.frameworks) > 0 else 0.0),
                    2
                )
            },
            "libraries": {
                "snapshot1_value": metrics1.libraries,
                "snapshot2_value": metrics2.libraries,
                "change": len(metrics2.libraries) - len(metrics1.libraries),
                "percent_change": round(
                    ((len(metrics2.libraries) - len(metrics1.libraries)) / len(metrics1.libraries) * 100)
                    if len(metrics1.libraries) > 0
                    else (100.0 if len(metrics2.libraries) > 0 else 0.0),
                    2
                )
            },
            "skills": {
                "snapshot1_value": metrics1.skill_count,
                "snapshot2_value": metrics2.skill_count,
                "change": metrics2.skill_count - metrics1.skill_count,
                "percent_change": round(
                    ((metrics2.skill_count - metrics1.skill_count) / metrics1.skill_count * 100)
                    if metrics1.skill_count > 0
                    else (100.0 if metrics2.skill_count > 0 else 0.0),
                    2
                )
            },
            "total_files": {
                "snapshot1_value": metrics1.total_files,
                "snapshot2_value": metrics2.total_files,
                "change": metrics2.total_files - metrics1.total_files,
                "percent_change": round(
                    ((metrics2.total_files - metrics1.total_files) / metrics1.total_files * 100)
                    if metrics1.total_files > 0
                    else (100.0 if metrics2.total_files > 0 else 0.0),
                    2
                )
            },
            "total_loc": {
                "snapshot1_value": metrics1.total_loc,
                "snapshot2_value": metrics2.total_loc,
                "change": metrics2.total_loc - metrics1.total_loc,
                "percent_change": round(
                    ((metrics2.total_loc - metrics1.total_loc) / metrics1.total_loc * 100)
                    if metrics1.total_loc > 0
                    else (100.0 if metrics2.total_loc > 0 else 0.0),
                    2
                )
            },
            "avg_complexity": {
                "snapshot1_value": metrics1.avg_complexity or 0.0,
                "snapshot2_value": metrics2.avg_complexity or 0.0,
                "change": (metrics2.avg_complexity or 0.0) - (metrics1.avg_complexity or 0.0),
                "percent_change": round(
                    (((metrics2.avg_complexity or 0.0) - (metrics1.avg_complexity or 0.0)) / (metrics1.avg_complexity or 1.0) * 100)
                    if (metrics1.avg_complexity or 0.0) > 0
                    else 0.0,
                    2
                )
            },
        }

        return {
            "metric_changes": metric_changes,
            "new_languages": new_languages,
            "new_frameworks": new_frameworks,
            "new_libraries": new_libraries,
            "new_contributors": new_contributors,
        }

    def _generate_summary(
        self,
        metrics1: SnapshotMetrics,
        metrics2: SnapshotMetrics,
        comparison_data: dict
    ) -> str:
        """Generate human-readable summary of changes."""
        parts = []

        # File changes
        file_change = metrics2.total_files - metrics1.total_files
        if file_change > 0:
            file_percent = round(file_change / metrics1.total_files * 100, 1) if metrics1.total_files > 0 else 0
            parts.append(f"Project grew by {file_change} files ({file_percent}% increase)")

        # Technology changes
        new_langs = comparison_data["new_languages"]
        new_fws = comparison_data["new_frameworks"]
        new_libs = comparison_data["new_libraries"]

        if new_langs:
            parts.append(f"added {len(new_langs)} new language{'s' if len(new_langs) > 1 else ''} ({', '.join(new_langs)})")

        if new_fws:
            parts.append(f"{len(new_fws)} new framework{'s' if len(new_fws) > 1 else ''} ({', '.join(new_fws)})")

        if new_libs:
            parts.append(f"{len(new_libs)} new librar{'ies' if len(new_libs) > 1 else 'y'}")

        # LOC changes
        loc_change = metrics2.total_loc - metrics1.total_loc
        if loc_change > 0:
            loc_percent = round(loc_change / metrics1.total_loc * 100, 1) if metrics1.total_loc > 0 else 0
            parts.append(f"Lines of code increased by {loc_change} ({loc_percent}%)")

        if not parts:
            return "No significant changes detected between snapshots."

        return ". ".join(parts) + "."
