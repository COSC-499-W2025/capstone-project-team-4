"""Service for orchestrating snapshot creation and analysis workflow."""

import logging
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from src.core.snapshot_manager import SnapshotManager
from src.models.orm import Snapshot, Project
from src.models.schemas.analysis import AnalysisResult
from src.repositories.project_repository import ProjectRepository
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
        self.project_repo = ProjectRepository(db)

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

            # Step 1: Create source project (metadata only, not analyzed)
            source_project = Project(
                name=project_name,
                root_path=str(project_path),
                source_type="upload",
                snapshot_id=None  # This is the source, not a snapshot
            )
            self.db.add(source_project)
            self.db.commit()
            self.db.refresh(source_project)
            logger.info(f"Created source project (ID: {source_project.id})")

            # Calculate snapshot points (only "Old" - 50%)
            snapshot_points = snapshot_manager.calculate_snapshot_points()

            # Create and analyze snapshots
            analysis_results = []
            snapshot_records = []  # Track Snapshot ORM objects
            today = datetime.now().strftime("%Y-%m-%d")

            # Step 2: Create "Old" snapshot (50% of history)
            for snapshot_label, commit_index in snapshot_points:
                commit_hash = commits[commit_index].split()[0]
                commit_percentage = 50.0  # Old is at 50%

                logger.info(f"Creating '{snapshot_label}' snapshot at commit {commit_hash} ({commit_percentage}% of history)")

                # Create Snapshot record with metadata
                snapshot = Snapshot(
                    source_project_id=source_project.id,
                    snapshot_type="baseline",
                    label=f"{today} {snapshot_label}",
                    commit_hash=commit_hash,
                    commit_percentage=commit_percentage,
                    snapshot_date=datetime.utcnow()
                )
                self.db.add(snapshot)
                self.db.commit()
                self.db.refresh(snapshot)
                snapshot_records.append(snapshot)

                # Create snapshot directory
                snapshot_project_path = snapshot_manager.create_snapshot(
                    commit_hash,
                    snapshot_label,
                    temp_dir
                )

                # Analyze snapshot (creates Project with analysis data)
                # Use project name with snapshot label for backward compatibility
                snapshot_project_name = f"{project_name}-{snapshot_label}"
                result = self.analysis_service.analyze_from_directory(snapshot_project_path, snapshot_project_name)

                # Link the analyzed project to the snapshot
                if isinstance(result, list):
                    for r in result:
                        project = self.project_repo.get(r.project_id)
                        project.snapshot_id = snapshot.id
                        self.project_repo.update(project)
                    analysis_results.extend(result)
                else:
                    project = self.project_repo.get(result.project_id)
                    project.snapshot_id = snapshot.id
                    self.project_repo.update(project)
                    analysis_results.append(result)

            # Step 3: Analyze "Current" snapshot (uploaded version, no rewind)
            logger.info(f"Analyzing 'Current' snapshot using uploaded version (HEAD)")

            # Create Snapshot record for Current
            snapshot = Snapshot(
                source_project_id=source_project.id,
                snapshot_type="current",
                label=f"{today} Current",
                commit_hash=commits[0].split()[0] if commits else None,  # Latest commit
                commit_percentage=100.0,
                snapshot_date=datetime.utcnow()
            )
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            snapshot_records.append(snapshot)

            # Analyze the project as-is (at HEAD)
            # Use project name with snapshot label for backward compatibility
            current_project_name = f"{project_name}-Current"
            result = self.analysis_service.analyze_from_directory(project_path, current_project_name)

            # Link the analyzed project to the snapshot
            if isinstance(result, list):
                for r in result:
                    project = self.project_repo.get(r.project_id)
                    project.snapshot_id = snapshot.id
                    self.project_repo.update(project)
                analysis_results.extend(result)
            else:
                project = self.project_repo.get(result.project_id)
                project.snapshot_id = snapshot.id
                self.project_repo.update(project)
                analysis_results.append(result)

            # Step 4: Automatically create comparison between snapshots
            if len(snapshot_records) == 2:
                try:
                    snapshot_service = SnapshotService(self.db)
                    comparison = snapshot_service.create_comparison(
                        snapshot_records[0].id,  # Snapshot ID, not Project ID
                        snapshot_records[1].id
                    )
                    logger.info(
                        f"Created automatic comparison (ID: {comparison.id}) "
                        f"between snapshots {snapshot_records[0].id} and {snapshot_records[1].id}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to create automatic comparison: {e}")
                    # Don't fail the whole operation if comparison fails

            logger.info(f"Completed snapshot analysis with {len(analysis_results)} snapshots")
            return analysis_results
