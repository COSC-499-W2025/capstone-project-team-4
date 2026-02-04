"""Service for orchestrating snapshot creation and analysis workflow."""

import logging
import tempfile
import zipfile
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from src.core.snapshot_manager import SnapshotManager
from src.models.schemas.analysis import AnalysisResult
from src.services.analysis_service import AnalysisService
from src.services.snapshot_service import SnapshotService

logger = logging.getLogger(__name__)


class SnapshotAnalysisService:
    """Orchestrates snapshot creation, analysis, and comparison."""

    def __init__(self, db: Session):
        """
        Initialize snapshot analysis service.

        Args:
            db: Database session
        """
        self.db = db
        self.analysis_service = AnalysisService(db)

    def analyze_with_snapshots(
        self,
        zip_path: Path,
        project_name: str
    ) -> List[AnalysisResult]:
        """
        Analyze a project and create snapshots at different commit points.

        This method:
        1. Extracts and validates the ZIP file
        2. Validates git history (requires .git and 10+ commits)
        3. Creates snapshots:
           - Old: Rewinds to 50% of commit history
           - Current: Uses the uploaded version (HEAD/latest)
        4. Analyzes each snapshot
        5. Automatically creates comparison between snapshots

        Args:
            zip_path: Path to the ZIP file containing the project
            project_name: Base name for the project (snapshots will be named {name}-Old, {name}-Current)

        Returns:
            List of AnalysisResult objects (one per snapshot)

        Raises:
            ValueError: If project doesn't have git history or minimum commits
            RuntimeError: If git operations fail
        """
        logger.info(f"Starting snapshot analysis for project: {project_name}")

        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)

            # Extract ZIP file
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir()

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Find project directory
            project_dirs = list(extract_dir.iterdir())
            if not project_dirs:
                raise ValueError("Empty ZIP archive")

            project_path = project_dirs[0]

            # Initialize snapshot manager
            snapshot_manager = SnapshotManager(project_path, 0)

            # Get and validate git history
            commits = snapshot_manager.get_commit_history()
            total_commits = len(commits)

            # Recreate manager with actual commit count
            snapshot_manager = SnapshotManager(project_path, total_commits)
            snapshot_manager.validate_project()

            logger.info(f"Found {total_commits} commits in project history")

            # Calculate snapshot points (only "Old" - 50%)
            snapshot_points = snapshot_manager.calculate_snapshot_points()

            # Create and analyze snapshots
            analysis_results = []
            snapshot_ids = []

            # 1. Create "Old" snapshot (50% of history)
            for snapshot_label, commit_index in snapshot_points:
                commit_hash = commits[commit_index].split()[0]
                snapshot_name = f"{project_name}-{snapshot_label}"

                logger.info(f"Creating snapshot '{snapshot_label}' at commit {commit_hash} (50% of history)")

                # Create snapshot
                snapshot_project_path = snapshot_manager.create_snapshot(
                    commit_hash,
                    snapshot_label,
                    temp_dir
                )

                # Analyze snapshot
                result = self.analysis_service.analyze_from_directory(snapshot_project_path, snapshot_name)

                if isinstance(result, list):
                    analysis_results.extend(result)
                    snapshot_ids.extend([r.project_id for r in result])
                else:
                    analysis_results.append(result)
                    snapshot_ids.append(result.project_id)

            # 2. Analyze "Current" snapshot (uploaded version, no rewind)
            current_name = f"{project_name}-Current"
            logger.info(f"Analyzing 'Current' snapshot using uploaded version (HEAD)")

            # Analyze the project as-is (at HEAD)
            result = self.analysis_service.analyze_from_directory(project_path, current_name)

            if isinstance(result, list):
                analysis_results.extend(result)
                snapshot_ids.extend([r.project_id for r in result])
            else:
                analysis_results.append(result)
                snapshot_ids.append(result.project_id)

            # Automatically create comparison between snapshots
            if len(snapshot_ids) == 2:
                try:
                    snapshot_service = SnapshotService(self.db)
                    comparison = snapshot_service.create_comparison(
                        snapshot_ids[0],
                        snapshot_ids[1]
                    )
                    logger.info(
                        f"Created automatic comparison (ID: {comparison.id}) "
                        f"between snapshots {snapshot_ids[0]} and {snapshot_ids[1]}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to create automatic comparison: {e}")
                    # Don't fail the whole operation if comparison fails

            logger.info(f"Completed snapshot analysis with {len(analysis_results)} snapshots")
            return analysis_results
