"""Snapshot creation and management logic."""

import logging
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Handles creation of project snapshots at different commit points."""

    def __init__(self, project_path: Path, total_commits: int):
        """
        Initialize snapshot manager.

        Args:
            project_path: Path to the extracted project directory
            total_commits: Total number of commits in the project
        """
        self.project_path = project_path
        self.total_commits = total_commits
        self.temp_dir = None

    def validate_project(self) -> None:
        """
        Validate that project has git history and minimum commits.

        Raises:
            ValueError: If validation fails
        """
        # Verify .git directory exists
        git_dir = self.project_path / ".git"
        if not git_dir.exists():
            raise ValueError(
                "No .git directory found. Snapshot creation requires git history."
            )

        # Validate minimum commits
        if self.total_commits < 10:
            raise ValueError(
                f"Project has only {self.total_commits} commits. "
                f"Need at least 10 commits for snapshots."
            )

    def get_commit_history(self) -> List[str]:
        """
        Get git commit history.

        Returns:
            List of commit hashes in chronological order

        Raises:
            RuntimeError: If git command fails
        """
        # Convert path for git on Windows
        git_project_path = (
            str(self.project_path).replace("\\", "/")
            if platform.system() == "Windows"
            else str(self.project_path)
        )

        try:
            result = subprocess.run(
                ["git", "-C", git_project_path, "log", "--reverse", "--oneline", "--all"],
                capture_output=True,
                text=True,
                check=True,
            )

            commits = result.stdout.strip().split("\n")
            if not commits or not commits[0]:
                raise ValueError("No git commits found in project")

            return commits

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise RuntimeError(f"Failed to get git history: {e.stderr}")

    def calculate_snapshot_points(self) -> List[Tuple[str, int]]:
        """
        Calculate commit indices for snapshots.

        Returns:
            List of (label, commit_index) tuples
            Note: "Current" will be handled separately (uses HEAD/uploaded version)
        """
        return [
            ("Old", int(self.total_commits * 0.50)),  # 50% through history
            # "Current" snapshot uses the uploaded version (HEAD), not a specific commit
        ]

    def create_snapshot(
        self,
        commit_hash: str,
        snapshot_label: str,
        temp_dir_path: Path
    ) -> Path:
        """
        Create a snapshot at a specific commit.

        Args:
            commit_hash: Git commit hash to reset to
            snapshot_label: Label for this snapshot (e.g., "Mid", "Late")
            temp_dir_path: Temporary directory to create snapshot in

        Returns:
            Path to the created snapshot directory

        Raises:
            RuntimeError: If snapshot creation fails
        """
        # Create snapshot directory
        snapshot_dir = temp_dir_path / f"snapshot_{snapshot_label}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_project_path = snapshot_dir / "project"

        try:
            # Copy entire project directory (including .git)
            # Use symlinks=True on Unix, False on Windows (requires admin on Windows)
            use_symlinks = platform.system() != "Windows"
            shutil.copytree(self.project_path, snapshot_project_path, symlinks=use_symlinks)

            # Reset to specific commit
            git_snapshot_path = (
                str(snapshot_project_path).replace("\\", "/")
                if platform.system() == "Windows"
                else str(snapshot_project_path)
            )

            subprocess.run(
                ["git", "-C", git_snapshot_path, "reset", "--hard", commit_hash],
                capture_output=True,
                check=True,
            )

            # Clean build artifacts to speed up analysis
            self._clean_build_artifacts(snapshot_project_path)

            logger.info(f"Created snapshot at {commit_hash} ({snapshot_label})")
            return snapshot_project_path

        except Exception as e:
            logger.error(f"Failed to create snapshot {snapshot_label}: {e}")
            raise RuntimeError(f"Snapshot creation failed: {e}")

    def _clean_build_artifacts(self, project_path: Path) -> None:
        """
        Remove common build artifacts and dependencies.

        Args:
            project_path: Path to project directory
        """
        artifact_dirs = [
            "node_modules",
            "venv",
            "__pycache__",
            ".pytest_cache",
            "dist",
            "build",
            ".next",
            "target",  # Rust
            "vendor",  # Go, PHP
        ]

        for artifact_dir in artifact_dirs:
            artifact_path = project_path / artifact_dir
            if artifact_path.exists():
                try:
                    shutil.rmtree(artifact_path, ignore_errors=True)
                    logger.debug(f"Cleaned artifact: {artifact_dir}")
                except Exception as e:
                    logger.warning(f"Could not clean {artifact_dir}: {e}")
