"""Service for contributor analysis including top areas and top files."""

import logging
import os
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from src.models.orm.contributor import Contributor, ContributorFile
from src.models.schemas.contributor import (
    AreaShareSchema,
    ContributorAnalysisDetailResponseSchema,
    ContributorAnalysisDetailSchema,
    ContributorSummarySchema,
    TopFileItemSchema,
)
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.project_repository import ProjectRepository

logger = logging.getLogger(__name__)


class ContributorAnalysisService:
    """Service for analyzing individual contributor contributions."""

    def __init__(self, db):
        """Initialize service with database session."""
        self.db = db
        self.contributor_repo = ContributorRepository(db)
        self.project_repo = ProjectRepository(db)
        self._domain_mapping = None

    def _load_domain_mapping(self) -> Dict[str, Dict[str, List[str]]]:
        """Load domain mapping from YAML file."""
        if self._domain_mapping is not None:
            return self._domain_mapping

        mapping_path = Path(__file__).parent.parent / "config" / "domain_mapping.yaml"

        try:
            with open(mapping_path, "r") as f:
                self._domain_mapping = yaml.safe_load(f) or {}
                logger.info("Loaded domain mapping from %s", mapping_path)
        except Exception as e:
            logger.warning("Failed to load domain mapping: %s", e)
            self._domain_mapping = {}

        return self._domain_mapping

    def _classify_file_to_area(self, filename: str) -> Optional[str]:
        """Classify a file to an area based on domain mapping."""
        domain_config = self._load_domain_mapping()

        filename_lower = filename.lower()

        # Check by path prefix (most specific)
        for area, config in domain_config.items():
            paths = config.get("paths", [])
            for path_pattern in paths:
                if filename_lower.startswith(path_pattern.lower()):
                    return area

        # Check by file extension
        _, ext = os.path.splitext(filename)
        if ext:
            for area, config in domain_config.items():
                extensions = config.get("extensions", [])
                if ext.lower() in [e.lower() for e in extensions]:
                    return area

        return None

    def _is_valid_git_repo(self, repo_path: str) -> bool:
        if not repo_path or not Path(repo_path).exists():
            return False

        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and result.stdout.strip() == "true"
        except Exception:
            return False

    def _calculate_top_files_from_db(
        self, contributor_id: int, top_n: int = 10
    ) -> List[TopFileItemSchema]:
        files = self.contributor_repo.get_with_files(contributor_id)
        if not files or not files.files_modified:
            return []

        file_stats = []
        for file_obj in files.files_modified:
            filename = file_obj.filename
            modifications = file_obj.modifications or 0
            if modifications > 0:
                file_stats.append((filename, modifications))

        file_stats.sort(key=lambda x: x[1], reverse=True)
        top_files = file_stats[:top_n]

        return [
            TopFileItemSchema(file=filename, lines_changed=modifications)
            for filename, modifications in top_files
        ]

    def _calculate_top_areas_from_db(self, contributor_id: int) -> List[AreaShareSchema]:
        files = self.contributor_repo.get_with_files(contributor_id)
        if not files or not files.files_modified:
            return []

        area_stats: Dict[str, int] = defaultdict(int)
        for file_obj in files.files_modified:
            filename = file_obj.filename
            modifications = file_obj.modifications or 0
            if modifications <= 0:
                continue
            area = self._classify_file_to_area(filename)
            if area:
                area_stats[area] += modifications

        if not area_stats:
            return []

        total_lines = sum(area_stats.values())
        if total_lines == 0:
            return []

        top_areas = [
            AreaShareSchema(area=area, share=round(count / total_lines, 4))
            for area, count in area_stats.items()
        ]
        top_areas.sort(key=lambda x: x.share, reverse=True)
        return top_areas

    def _get_file_lines_changed(
        self,
        repo_path: str,
        filename: str,
        contributor_email: str,
        branch: str = "HEAD",
    ) -> int:
        """Get total lines changed for a specific file by a contributor.

        Args:
            repo_path: Path to git repository
            filename: File path to analyze
            contributor_email: Contributor's email to filter commits
            branch: Branch to analyze

        Returns:
            Total lines changed (added + deleted)
        """
        # Log every call (commented out for performance, enable for debugging)
        # logger.info(f"_get_file_lines_changed: {filename} by {contributor_email}")

        try:
            # Use git log with case-insensitive author search (-i flag)
            # This ensures we match emails regardless of case differences
            cmd = [
                "git",
                "-C",
                repo_path,
                "log",
                "-i",  # Case-insensitive matching
                branch,
                f"--author={contributor_email}",
                "--numstat",
                "--pretty=%aN <%aE>",
            ]

            logger.debug("Running git command: %s", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.warning(
                    "Git command failed for %s: returncode=%s, stderr=%s",
                    filename,
                    result.returncode,
                    result.stderr,
                )
                return 0

            if not result.stdout.strip():
                logger.debug("No git output for %s with email %s", filename, contributor_email)
                return 0

            total_added = 0
            total_deleted = 0

            # Parse the output line by line
            lines = result.stdout.strip().split("\n")
            current_author = None

            for line in lines:
                if not line.strip():
                    continue

                # Check if this is an author line (contains email)
                if "<" in line and ">" in line:
                    current_author = line.strip()
                    continue

                # This should be a numstat line (starts with numbers or -)
                if current_author:
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        added_str, deleted_str, file_in_commit = parts[0], parts[1], parts[2]

                        # Skip binary files
                        if added_str == "-" or deleted_str == "-":
                            continue

                        file_normalized = file_in_commit.strip()
                        filename_normalized = filename.strip()

                        # Check if this is the file we're looking for
                        # Use exact path matching to avoid matching different files with same basename
                        # (e.g., skill.py in different directories)
                        if (
                            file_normalized == filename_normalized
                            or file_normalized.endswith("/" + filename_normalized)
                            or file_normalized.endswith("\\" + filename_normalized)
                        ):
                            try:
                                added = int(added_str)
                                deleted = int(deleted_str)
                                total_added += added
                                total_deleted += deleted
                                logger.debug(
                                    "  Match: %s -> +%d -%d",
                                    file_in_commit,
                                    added,
                                    deleted,
                                )
                            except ValueError:
                                pass

            logger.debug(
                "File %s: total_added=%d, total_deleted=%d, total=%d",
                filename,
                total_added,
                total_deleted,
                total_added + total_deleted,
            )
            return total_added + total_deleted

        except subprocess.TimeoutExpired:
            logger.warning("Git command timed out for file %s", filename)
            return 0
        except Exception as e:
            logger.debug("Error getting file stats for %s: %s", filename, e)
            return 0

    def calculate_top_files(
        self,
        contributor_id: int,
        repo_path: str,
        branch: str = "HEAD",
        top_n: int = 10,
    ) -> List[TopFileItemSchema]:
        """Calculate top files by lines changed for a contributor.

        Args:
            contributor_id: Contributor ID
            repo_path: Path to git repository
            branch: Branch to analyze
            top_n: Number of top files to return

        Returns:
            List of top files sorted by lines changed (descending)
        """
        # Get contributor
        contributor = self.contributor_repo.get(contributor_id)
        if not contributor or not contributor.email:
            logger.warning("Contributor %s not found or has no email", contributor_id)
            return []

        logger.info(
            "Calculating top files for contributor %s (email: %s), repo: %s, branch: %s",
            contributor_id,
            contributor.email,
            repo_path,
            branch,
        )

        # Get all files modified by this contributor
        files = self.contributor_repo.get_with_files(contributor_id)
        if not files or not files.files_modified:
            logger.debug("No files found for contributor %s", contributor_id)
            return []

        logger.info(
            "Found %d files modified by contributor %s",
            len(files.files_modified),
            contributor_id,
        )

        # Calculate lines changed for each file
        file_stats: List[Tuple[str, int]] = []

        for idx, file_obj in enumerate(files.files_modified):
            filename = file_obj.filename
            lines_changed = self._get_file_lines_changed(
                repo_path, filename, contributor.email, branch
            )

            # Log details for first file only (for debugging)
            if idx == 0:
                logger.info("FIRST FILE DEBUG: %s", filename)
                logger.info("  repo_path=%s", repo_path)
                logger.info("  contributor.email=%s", contributor.email)
                logger.info("  branch=%s", branch)
                logger.info("  lines_changed=%d", lines_changed)

            # Log files with changes or sample files
            if idx < 10 or lines_changed > 0:
                logger.info(
                    "  [%d/%d] %s: %d lines",
                    idx + 1,
                    len(files.files_modified),
                    filename,
                    lines_changed,
                )

            if lines_changed > 0:
                file_stats.append((filename, lines_changed))

        logger.info(
            "Found %d files with actual changes (total: %d files)",
            len(file_stats),
            len(files.files_modified),
        )

        # Sort by lines changed descending and take top N
        file_stats.sort(key=lambda x: x[1], reverse=True)
        top_files = file_stats[:top_n]

        logger.info(
            "Returning %d top files out of %d total",
            len(top_files),
            len(file_stats),
        )

        return [
            TopFileItemSchema(file=filename, lines_changed=lines_changed)
            for filename, lines_changed in top_files
        ]

    def calculate_top_areas(
        self, contributor_id: int, repo_path: str, branch: str = "HEAD"
    ) -> List[AreaShareSchema]:
        """Calculate top contributing areas for a contributor.

        Args:
            contributor_id: Contributor ID
            repo_path: Path to git repository
            branch: Branch to analyze

        Returns:
            List of areas with their share (0-1.0) sorted by share descending
        """
        # Get contributor
        contributor = self.contributor_repo.get(contributor_id)
        if not contributor or not contributor.email:
            logger.warning("Contributor %s not found or has no email", contributor_id)
            return []

        logger.info(
            "Calculating top areas for contributor %s (email: %s), repo: %s, branch: %s",
            contributor_id,
            contributor.email,
            repo_path,
            branch,
        )

        # Get all files modified by this contributor
        files = self.contributor_repo.get_with_files(contributor_id)
        if not files or not files.files_modified:
            logger.debug("No files found for contributor %s", contributor_id)
            return []

        logger.info(
            "Found %d files modified by contributor %s",
            len(files.files_modified),
            contributor_id,
        )

        # Calculate lines changed for each file
        file_stats: Dict[str, int] = {}
        for file_obj in files.files_modified:
            filename = file_obj.filename
            lines_changed = self._get_file_lines_changed(
                repo_path, filename, contributor.email, branch
            )
            if lines_changed > 0:
                file_stats[filename] = lines_changed

        if not file_stats:
            logger.warning("No file stats found for contributor %s", contributor_id)
            return []

        logger.info("Found %d files with actual changes", len(file_stats))

        # Group files by area
        area_stats: Dict[str, int] = defaultdict(int)
        for filename, lines_changed in file_stats.items():
            area = self._classify_file_to_area(filename)
            logger.debug("  %s -> %s: %d lines", filename, area, lines_changed)
            if area:
                area_stats[area] += lines_changed

        if not area_stats:
            logger.warning("No areas classified for contributor %s", contributor_id)
            return []

        logger.info("Classified into %d areas", len(area_stats))

        # Calculate shares
        total_lines = sum(area_stats.values())
        if total_lines == 0:
            return []

        top_areas = [
            AreaShareSchema(area=area, share=round(count / total_lines, 4))
            for area, count in area_stats.items()
        ]

        # Sort by share descending
        top_areas.sort(key=lambda x: x.share, reverse=True)

        logger.info("Returning %d areas", len(top_areas))

        return top_areas

    def get_contributor_analysis(
        self,
        project_id: int,
        contributor_id: int,
        branch: Optional[str] = None,
    ) -> Optional[ContributorAnalysisDetailResponseSchema]:
        """Get analysis for a specific contributor.

        Args:
            project_id: Project ID
            contributor_id: Contributor ID
            branch: Branch to analyze (optional)

        Returns:
            ContributorAnalysisDetailResponseSchema or None if not found
        """
        # Verify project exists
        project = self.project_repo.get(project_id)
        if not project:
            logger.warning("Project %s not found", project_id)
            return None

        # Verify contributor exists and belongs to project
        contributor = self.contributor_repo.get(contributor_id)
        if not contributor:
            logger.warning("Contributor %s not found", contributor_id)
            return None

        if contributor.project_id != project_id:
            logger.warning(
                "Contributor %s does not belong to project %s",
                contributor_id,
                project_id,
            )
            return None

        # Determine branch to analyze
        repo_path = project.root_path
        if not branch:
            # Try to determine default branch from git
            try:
                cmd = [
                    "git",
                    "-C",
                    repo_path,
                    "rev-parse",
                    "--abbrev-ref",
                    "HEAD",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    branch = result.stdout.strip()
                else:
                    branch = "HEAD"
            except Exception as e:
                logger.debug("Failed to determine default branch: %s", e)
                branch = "HEAD"

        logger.info("PROJECT INFO:")
        logger.info("  project.root_path=%s", project.root_path)
        logger.info("  repo_path=%s", repo_path)
        logger.info("  branch=%s", branch)
        logger.info("  contributor.email=%s", contributor.email)

        use_git = self._is_valid_git_repo(repo_path)
        if not use_git:
            logger.warning("Repo path is not a valid git repo: %s", repo_path)

        # Calculate top areas and top files
        if use_git:
            top_areas = self.calculate_top_areas(contributor_id, repo_path, branch)
            top_files = self.calculate_top_files(contributor_id, repo_path, branch, top_n=10)
        else:
            top_areas = self._calculate_top_areas_from_db(contributor_id)
            top_files = self._calculate_top_files_from_db(contributor_id, top_n=10)

        # Build response
        summary = ContributorSummarySchema(
            top_areas=top_areas,
            top_files=top_files,
        )

        contributor_detail = ContributorAnalysisDetailSchema(
            contributor_id=contributor_id,
            name=contributor.name,
            summary=summary,
        )

        return ContributorAnalysisDetailResponseSchema(
            project_id=project_id,
            project_name=project.name,
            branch=branch,
            contributor=contributor_detail,
            generated_at=datetime.utcnow(),
        )
