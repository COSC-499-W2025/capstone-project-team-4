"""Service for managing snapshot comparisons."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.models.orm import Project, Snapshot, SnapshotComparison
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
            ValueError: If snapshots don't exist or don't have analyzed projects
        """
        # Get Snapshot objects
        snapshot1 = self.db.query(Snapshot).filter_by(id=snapshot1_id).first()
        snapshot2 = self.db.query(Snapshot).filter_by(id=snapshot2_id).first()

        if not snapshot1:
            raise ValueError(f"Project 1 not found: ID {snapshot1_id}")
        if not snapshot2:
            raise ValueError(f"Project 2 not found: ID {snapshot2_id}")

        # Get the analyzed project data from snapshots
        project1 = snapshot1.analyzed_project
        project2 = snapshot2.analyzed_project

        if not project1:
            raise ValueError(f"Snapshot 1 (ID {snapshot1_id}) has no analyzed project data")
        if not project2:
            raise ValueError(f"Snapshot 2 (ID {snapshot2_id}) has no analyzed project data")

        # Convert to metrics
        metrics1 = self._convert_to_snapshot_metrics(project1, snapshot1)
        metrics2 = self._convert_to_snapshot_metrics(project2, snapshot2)

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

        logger.info(f"Created comparison between snapshots {snapshot1_id} and {snapshot2_id}")
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

        # Get Snapshot objects and their analyzed projects
        snapshot1 = self.db.query(Snapshot).filter_by(id=snapshot1_id).first()
        snapshot2 = self.db.query(Snapshot).filter_by(id=snapshot2_id).first()

        if not snapshot1 or not snapshot2:
            raise ValueError("One or both snapshots not found")

        project1 = snapshot1.analyzed_project
        project2 = snapshot2.analyzed_project

        if not project1 or not project2:
            raise ValueError("One or both snapshots have no analyzed project data")

        metrics1 = self._convert_to_snapshot_metrics(project1, snapshot1)
        metrics2 = self._convert_to_snapshot_metrics(project2, snapshot2)

        # Build response
        metric_changes = comparison.metric_changes

        return SnapshotComparisonSchema(
            snapshot1_name=snapshot1.label,
            snapshot2_name=snapshot2.label,
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

    def _convert_to_snapshot_metrics(self, project: Project, snapshot: Snapshot) -> SnapshotMetrics:
        """Convert Project ORM and Snapshot to SnapshotMetrics.

        Args:
            project: The analyzed project data
            snapshot: The snapshot metadata
        """
        # Get complexity summary
        complexity_summary = self.complexity_repo.get_summary(project.id)

        # Get contributor count
        contributor_count = self.contributor_repo.count_by_project(project.id)

        # Get lists from project repository
        languages = self.project_repo.get_languages(project.id)
        frameworks = self.project_repo.get_frameworks(project.id)
        libraries = self.project_repo.get_libraries(project.id)
        tools = self.project_repo.get_tools(project.id)

        # Get skill count
        skill_count = self.skill_repo.count_by_project(project.id)

        # Get total LOC
        total_loc = self.project_repo.get_total_lines_of_code(project.id)

        return SnapshotMetrics(
            snapshot_name=snapshot.label,  # Use snapshot label instead of project name
            total_commits=contributor_count,  # Use contributor count as proxy for commits
            contributor_count=contributor_count,
            languages=languages,
            frameworks=frameworks,
            libraries=libraries,
            tools=tools,
            skill_count=skill_count,
            total_files=len(project.files) if project.files else 0,
            total_loc=total_loc,
            avg_complexity=complexity_summary.get("avg_complexity", 0.0),
            first_commit_date=project.first_commit_date.isoformat() if project.first_commit_date else None,
        )

    def _calculate_comparisons(self, metrics1: SnapshotMetrics, metrics2: SnapshotMetrics) -> dict:
        """Calculate metric comparisons and new items."""
        def calc_change(val1, val2, is_list=False):
            """Calculate absolute change and percent change for a metric.

            Args:
                val1: Value from snapshot 1 (can be int, float, or list)
                val2: Value from snapshot 2 (can be int, float, or list)
                is_list: If True, preserves list values and calculates change based on length
            """
            # For list metrics, preserve the lists but calculate change based on length
            if is_list:
                snapshot1_val = val1
                snapshot2_val = val2
                val1_count = len(val1) if val1 else 0
                val2_count = len(val2) if val2 else 0
            else:
                snapshot1_val = val1 or 0.0
                snapshot2_val = val2 or 0.0
                val1_count = val1 or 0.0
                val2_count = val2 or 0.0

            change = val2_count - val1_count
            percent_change = (change / val1_count * 100) if val1_count > 0 else (100.0 if val2_count > 0 else 0.0)

            return {
                "snapshot1_value": snapshot1_val,
                "snapshot2_value": snapshot2_val,
                "change": change,
                "percent_change": round(percent_change, 2)
            }

        # Calculate new items
        new_languages = list(set(metrics2.languages) - set(metrics1.languages))
        new_frameworks = list(set(metrics2.frameworks) - set(metrics1.frameworks))
        new_libraries = list(set(metrics2.libraries) - set(metrics1.libraries))
        new_contributors = []  # Would need contributor names from database

        # Build metric changes using the helper function
        metric_changes = {
            "contributors": calc_change(metrics1.contributor_count, metrics2.contributor_count),
            "languages": calc_change(metrics1.languages, metrics2.languages, is_list=True),
            "frameworks": calc_change(metrics1.frameworks, metrics2.frameworks, is_list=True),
            "libraries": calc_change(metrics1.libraries, metrics2.libraries, is_list=True),
            "skills": calc_change(metrics1.skill_count, metrics2.skill_count),
            "total_files": calc_change(metrics1.total_files, metrics2.total_files),
            "total_loc": calc_change(metrics1.total_loc, metrics2.total_loc),
            "avg_complexity": calc_change(metrics1.avg_complexity, metrics2.avg_complexity),
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