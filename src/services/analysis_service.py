"""Analysis service - main orchestration for project analysis pipeline."""

import logging
import zipfile
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from src.models.schemas.analysis import AnalysisResult, AnalysisStatus, ComplexitySummary
from src.repositories.project_repository import ProjectRepository
from src.repositories.file_repository import FileRepository
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.complexity_repository import ComplexityRepository
from src.repositories.skill_repository import SkillRepository
from src.repositories.resume_repository import ResumeRepository

# Core analyzers - using existing modules
from src.core.metadata_parser import parse_metadata
from src.core.project_analyzer import (
    analyze_contributors as git_analyze_contributors,
    analyze_project,
    project_analysis_to_dict,
    calculate_project_stats,
)
from src.core.resume_skill_extractor import analyze_project_skills
from src.core.resume_item_generator import generate_resume_item

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for orchestrating project analysis."""

    def __init__(self, db: Session):
        """Initialize analysis service with database session."""
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.file_repo = FileRepository(db)
        self.contributor_repo = ContributorRepository(db)
        self.complexity_repo = ComplexityRepository(db)
        self.skill_repo = SkillRepository(db)
        self.resume_repo = ResumeRepository(db)

    def analyze_from_zip(
        self,
        zip_path: Path,
        project_name: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Analyze a project from a ZIP file.

        Args:
            zip_path: Path to the ZIP file
            project_name: Optional custom project name

        Returns:
            AnalysisResult with analysis data
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        if not zipfile.is_zipfile(zip_path):
            raise ValueError(f"Invalid ZIP file: {zip_path}")

        name = project_name or zip_path.stem

        # Extract to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Extracting ZIP to {temp_dir}")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(temp_dir)

            return self._run_analysis_pipeline(
                project_path=Path(temp_dir),
                project_name=name,
                source_type="zip",
                source_url=str(zip_path),
            )

    def analyze_from_directory(
        self,
        directory_path: Path,
        project_name: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Analyze a project from a local directory.

        Args:
            directory_path: Path to the project directory
            project_name: Optional custom project name

        Returns:
            AnalysisResult with analysis data
        """
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")

        name = project_name or directory_path.name

        return self._run_analysis_pipeline(
            project_path=directory_path,
            project_name=name,
            source_type="local",
            source_url=str(directory_path),
        )

    def analyze_from_github(
        self,
        github_url: str,
        branch: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Analyze a project from a GitHub repository.

        Args:
            github_url: GitHub repository URL
            branch: Optional branch to clone

        Returns:
            AnalysisResult with analysis data
        """
        # Parse GitHub URL
        parsed = urlparse(github_url)
        if "github.com" not in parsed.netloc:
            raise ValueError(f"Invalid GitHub URL: {github_url}")

        # Extract owner/repo from path
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL format: {github_url}")

        owner, repo = path_parts[0], path_parts[1]
        repo = repo.replace(".git", "")
        project_name = repo

        # Clone to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            clone_url = f"https://github.com/{owner}/{repo}.git"
            clone_path = Path(temp_dir) / repo

            logger.info(f"Cloning {clone_url} to {clone_path}")

            try:
                import subprocess
                cmd = ["git", "clone", "--depth", "100"]
                if branch:
                    cmd.extend(["--branch", branch])
                cmd.extend([clone_url, str(clone_path)])

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode != 0:
                    raise RuntimeError(f"Git clone failed: {result.stderr}")

            except subprocess.TimeoutExpired:
                raise RuntimeError("Git clone timed out")
            except FileNotFoundError:
                raise RuntimeError("Git is not installed or not in PATH")

            return self._run_analysis_pipeline(
                project_path=clone_path,
                project_name=project_name,
                source_type="github",
                source_url=github_url,
            )

    def _run_analysis_pipeline(
        self,
        project_path: Path,
        project_name: str,
        source_type: str,
        source_url: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Run the full analysis pipeline on a project.

        Args:
            project_path: Path to the project directory
            project_name: Name of the project
            source_type: Type of source (local, zip, github)
            source_url: URL or path of the source

        Returns:
            AnalysisResult with all analysis data
        """
        logger.info(f"Starting analysis for {project_name} at {project_path}")

        try:
            # Step 1: Parse metadata
            logger.info("Step 1: Parsing metadata")
            df, project_root = parse_metadata(str(project_path))
            file_list = df.to_dict(orient="records")

            # Calculate project stats
            project_stats = calculate_project_stats(project_root, file_list)

            # Step 2: Create project entry
            logger.info("Step 2: Creating project entry")
            project = self.project_repo.create_project(
                name=project_name,
                root_path=str(project_root),
                source_type=source_type,
                source_url=source_url,
            )
            project_id = project.id

            # Step 3: Analyze contributors from git history
            logger.info("Step 3: Analyzing contributors")
            contributors = []
            try:
                contributors = git_analyze_contributors(project_root)
            except Exception as e:
                logger.warning(f"Git analysis failed: {e}")

            # Step 4: Analyze code complexity
            logger.info("Step 4: Analyzing code complexity")
            complexity_dict = {"functions": []}
            try:
                complexity_dict = project_analysis_to_dict(analyze_project(project_path))
            except Exception as e:
                logger.warning(f"Complexity analysis failed: {e}")

            # Step 5: Extract skills
            logger.info("Step 5: Extracting skills")
            skill_report = {"languages": [], "frameworks": [], "skills": [], "skill_categories": {}}
            try:
                skill_report = analyze_project_skills(project_root)
            except Exception as e:
                logger.warning(f"Skill extraction failed: {e}")

            languages = sorted(set(skill_report.get("languages", [])))
            frameworks = sorted(set(skill_report.get("frameworks", [])))

            # Step 6: Save files to database
            logger.info("Step 6: Saving files to database")
            self._save_files(project_id, file_list)

            # Step 7: Save complexity to database
            logger.info("Step 7: Saving complexity to database")
            self._save_complexity(project_id, complexity_dict.get("functions", []))

            # Step 8: Save contributors to database
            logger.info("Step 8: Saving contributors to database")
            if contributors:
                self._save_contributors(project_id, contributors)

            # Step 9: Save skills to database
            logger.info("Step 9: Saving skills to database")
            self._save_skills(project_id, skill_report.get("skill_categories", {}))

            # Step 10: Generate and save resume item
            logger.info("Step 10: Generating resume item")
            resume_item = generate_resume_item(
                project_name=project_name,
                contributors=contributors,
                project_stats=project_stats,
                skill_categories=skill_report.get("skill_categories", {}),
                languages=languages,
                frameworks=frameworks,
                complexity_dict=complexity_dict,
            )
            self._save_resume_item(project_id, resume_item)

            # Build result
            complexity_summary = self.complexity_repo.get_summary(project_id)

            return AnalysisResult(
                project_id=project_id,
                project_name=project_name,
                status=AnalysisStatus.COMPLETED,
                source_type=source_type,
                source_url=source_url,
                languages=languages,
                frameworks=frameworks,
                file_count=len(file_list),
                contributor_count=len(contributors),
                skill_count=self.skill_repo.count_by_project(project_id),
                total_lines_of_code=project_stats.get("total_lines", 0),
                complexity_summary=ComplexitySummary(
                    total_functions=complexity_summary.get("total_functions", 0),
                    avg_complexity=complexity_summary.get("avg_complexity", 0.0),
                    max_complexity=complexity_summary.get("max_complexity", 0),
                    high_complexity_count=complexity_summary.get("high_complexity_count", 0),
                ),
                created_at=project.created_at,
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    def _save_files(self, project_id: int, file_list: list) -> None:
        """Save file metadata to database."""
        files_data = []
        for f in file_list:
            files_data.append({
                "project_id": project_id,
                "path": f.get("path", ""),
                "language_name": f.get("language"),
                "file_size": f.get("file_size"),
                "lines_of_code": f.get("lines_of_code"),
                "created_timestamp": f.get("created_timestamp"),
                "last_modified": f.get("last_modified"),
            })

        if files_data:
            self.file_repo.create_files_bulk(files_data)

    def _save_complexity(self, project_id: int, functions: list) -> None:
        """Save complexity metrics to database."""
        complexity_data = []
        for func in functions:
            complexity_data.append({
                "project_id": project_id,
                "file_path": func.get("file_path", ""),
                "function_name": func.get("function_name", "unknown"),
                "cyclomatic_complexity": func.get("cyclomatic_complexity", 1),
                "start_line": func.get("start_line"),
                "end_line": func.get("end_line"),
            })

        if complexity_data:
            self.complexity_repo.create_complexities_bulk(complexity_data)

    def _save_contributors(self, project_id: int, contributors: list) -> None:
        """Save contributor data to database."""
        contributors_data = []
        for c in contributors:
            files_modified = []
            for filename, mods in c.get("files_modified", {}).items():
                files_modified.append({
                    "filename": filename,
                    "modifications": mods,
                })

            contributors_data.append({
                "project_id": project_id,
                "name": c.get("name"),
                "email": c.get("email"),
                "commits": c.get("commits", 0),
                "percent": c.get("percent", 0.0),
                "total_lines_added": c.get("total_lines_added", 0),
                "total_lines_deleted": c.get("total_lines_deleted", 0),
                "files_modified": files_modified,
            })

        if contributors_data:
            self.contributor_repo.create_contributors_bulk(contributors_data)

    def _save_skills(self, project_id: int, skill_categories: dict) -> None:
        """Save skills to database."""
        skills_data = []
        for category, skills in skill_categories.items():
            for skill in skills:
                skills_data.append({
                    "project_id": project_id,
                    "skill": skill,
                    "category": category,
                    "frequency": 1,
                })

        if skills_data:
            self.skill_repo.create_skills_bulk(skills_data)

    def _save_resume_item(self, project_id: int, resume_item: dict) -> None:
        """Save resume item to database."""
        self.resume_repo.create_resume_item(
            project_id=project_id,
            title=resume_item.get("title", ""),
            highlights=resume_item.get("highlights", []),
        )

    def get_analysis_result(self, project_id: int) -> Optional[AnalysisResult]:
        """Get analysis result for a project."""
        project = self.project_repo.get(project_id)
        if not project:
            return None

        languages = self.project_repo.get_languages(project_id)
        frameworks = self.project_repo.get_frameworks(project_id)
        complexity_summary = self.complexity_repo.get_summary(project_id)

        return AnalysisResult(
            project_id=project_id,
            project_name=project.name,
            status=AnalysisStatus.COMPLETED,
            source_type=project.source_type,
            source_url=project.source_url,
            languages=languages,
            frameworks=frameworks,
            file_count=self.file_repo.count_by_project(project_id),
            contributor_count=self.contributor_repo.count_by_project(project_id),
            skill_count=self.skill_repo.count_by_project(project_id),
            total_lines_of_code=self.project_repo.get_total_lines_of_code(project_id),
            complexity_summary=ComplexitySummary(
                total_functions=complexity_summary.get("total_functions", 0),
                avg_complexity=complexity_summary.get("avg_complexity", 0.0),
                max_complexity=complexity_summary.get("max_complexity", 0),
                high_complexity_count=complexity_summary.get("high_complexity_count", 0),
            ),
            created_at=project.created_at,
        )
