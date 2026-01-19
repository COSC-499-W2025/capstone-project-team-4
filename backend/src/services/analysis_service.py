"""Analysis service - main orchestration for project analysis pipeline."""

import logging
import zipfile
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from src.models.schemas.analysis import AnalysisResult, AnalysisStatus, ComplexitySummary
from src.config.settings import settings
from src.repositories.project_repository import ProjectRepository
from src.repositories.file_repository import FileRepository
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.complexity_repository import ComplexityRepository
from src.repositories.skill_repository import SkillRepository
from src.repositories.resume_repository import ResumeRepository
from src.repositories.library_repository import LibraryRepository
from src.repositories.tool_repository import ToolRepository
from src.repositories.framework_repository import FrameworkRepository

# Core analyzers
from src.core.detectors.metadata import parse_metadata
from src.core.analyzers.contributor import analyze_contributors as git_analyze_contributors
from src.core.analyzers.project_stats import (
    analyze_project,
    project_analysis_to_dict,
    calculate_project_stats,
)
from src.core.detectors.language import ProjectAnalyzer
from src.core.detectors.skill import analyze_project_skills
from src.core.validators.cross_validator import CrossValidator
from src.core.detectors.library import detect_libraries_recursive
from src.core.detectors.tool import detect_tools_recursive
from src.core.detectors.framework import detect_frameworks_recursive
from src.core.generators.resume import generate_resume_item
from src.core.utils.file_walker import (
    collect_all_file_info,
    file_info_to_metadata_dict,
    FileInfo,
)

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
        self.library_repo = LibraryRepository(db)
        self.tool_repo = ToolRepository(db)
        self.framework_repo = FrameworkRepository(db)

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

        This optimized pipeline:
        1. Collects all file info in a SINGLE pass (avoiding redundant walks)
        2. Runs Git, Complexity, and Skill analysis in PARALLEL

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
            # Step 0: Single-pass file collection (OPTIMIZATION)
            logger.info("Step 0: Collecting file info (single pass)")
            file_info_list = collect_all_file_info(project_path, show_progress=True)
            file_paths = [f.path for f in file_info_list]
            logger.info(f"Step 0 complete: Collected info for {len(file_info_list)} files")

            # Step 1: Convert file info to metadata format
            logger.info("Step 1: Building metadata from collected files")
            project_root = str(Path(project_path).resolve())
            file_list = [file_info_to_metadata_dict(f) for f in file_info_list]
            logger.info(f"Step 1 complete: {len(file_list)} files")

            # Step 2: Create project entry
            logger.info("Step 2: Creating project entry")
            project = self.project_repo.create_project(
                name=project_name,
                root_path=project_root,
                source_type=source_type,
                source_url=source_url,
            )
            project_id = project.id
            logger.info(f"Step 2 complete: Project ID {project_id}")

            # Steps 3-6: PARALLEL ANALYSIS (Git, Complexity, Languages, Frameworks, Libraries, Tools)
            logger.info("Steps 3-6: Running parallel analysis")

            # Default values in case of errors
            contributors = []
            complexity_dict = {"functions": []}
            library_report = {"libraries": [], "by_ecosystem": {}, "total_count": 0}
            tool_report = {"tools": [], "by_category": {}, "total_count": 0}
            languages_detected: List[str] = []
            frameworks_detected: List[dict] = []

            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {
                    executor.submit(git_analyze_contributors, project_root): "contributors",
                    executor.submit(
                        lambda: project_analysis_to_dict(analyze_project(project_path, file_paths))
                    ): "complexity",
                    executor.submit(detect_libraries_recursive, project_path): "libraries",
                    executor.submit(detect_tools_recursive, project_path): "tools",
                    executor.submit(lambda: ProjectAnalyzer().analyze_project_languages(project_root)): "languages",
                    executor.submit(self._detect_frameworks_best, project_path): "frameworks",
                }

                for future in as_completed(futures):
                    task_name = futures[future]
                    try:
                        result = future.result()
                        if task_name == "contributors":
                            contributors = result
                            logger.info(f"Git analysis complete: Found {len(contributors)} contributors")
                        elif task_name == "complexity":
                            complexity_dict = result
                            logger.info(f"Complexity analysis complete: Found {len(complexity_dict.get('functions', []))} functions")
                        elif task_name == "libraries":
                            library_report = result
                            logger.info(f"Library detection complete: Found {library_report.get('total_count', 0)} libraries")
                        elif task_name == "tools":
                            tool_report = result
                            logger.info(f"Tool detection complete: Found {tool_report.get('total_count', 0)} tools")
                        elif task_name == "languages":
                            languages_detected = sorted(
                                [lang for lang, count in result.items() if lang != "Unknown" and count > 0]
                            )
                            logger.info("Language detection complete: Found %d languages", len(languages_detected))
                        elif task_name == "frameworks":
                            frameworks_detected = result or []
                            logger.info("Framework detection complete: Found %d frameworks", len(frameworks_detected))
                    except Exception as e:
                        logger.warning(f"{task_name} analysis failed: {e}")

            logger.info("Steps 3-6 complete: Parallel analysis finished")

            # Step 5.5: Extract skills with pre-detected signals
            logger.info("Step 5.5: Extracting skills with library/tool context")
            framework_names = [fw.get("name") for fw in frameworks_detected if fw.get("name")]
            skill_report = analyze_project_skills(
                project_root,
                libraries=library_report.get("libraries", []),
                tools=tool_report.get("tools", []),
                languages=languages_detected,
                frameworks=framework_names,
            )
            logger.info("Step 5.5 complete: Found %d skills", skill_report.get("total_skills", 0))

            # Step 5.6: Cross-validate detections
            logger.info("Step 5.6: Cross-validating detections")
            validator = CrossValidator(
                languages=languages_detected,
                frameworks=frameworks_detected,
                libraries=library_report.get("libraries", []),
                tools=tool_report.get("tools", [])
            )
            enhanced_results = validator.get_enhanced_results()
            validation_summary = enhanced_results.validation_summary
            logger.info(
                "Step 5.6 complete: Cross-validation found %d boosted, %d gap-filled frameworks",
                validation_summary.get("frameworks_boosted", 0),
                validation_summary.get("gap_filled_frameworks", 0)
            )

            # Merge enhanced frameworks with gap-filled ones
            all_enhanced_frameworks = enhanced_results.get_all_frameworks()

            # Step 6: Calculate project stats (uses contributors from parallel analysis)
            logger.info("Step 6: Calculating project stats")
            project_stats = calculate_project_stats(project_root, file_list, contributors)
            logger.info("Step 6 complete")

            languages = sorted(set(languages_detected))
            # Use enhanced frameworks from cross-validation
            frameworks = sorted(set(fw.get("name", "") for fw in all_enhanced_frameworks if fw.get("name")))
            libraries = sorted({lib.get("name", "").strip() for lib in library_report.get("libraries", []) if lib.get("name")})
            tools_and_technologies = sorted({tool.get("name", "").strip() for tool in tool_report.get("tools", []) if tool.get("name")})
            contextual_skills = sorted([
                skill
                for skill, source in skill_report.get("skill_sources", {}).items()
                if source == "contextual"
            ])

            # Step 7: Save to database
            logger.info("Step 7: Saving to database")
            self._save_files(project_id, file_list)
            self._save_complexity(project_id, complexity_dict.get("functions", []))
            if contributors:
                self._save_contributors(project_id, contributors)
            self._save_skills(
                project_id,
                skill_report.get("skill_categories", {}),
                skill_sources=skill_report.get("skill_sources", {}),
            )
            self._save_frameworks(project_id, all_enhanced_frameworks)
            self._save_libraries(project_id, library_report.get("libraries", []))
            self._save_tools(project_id, tool_report.get("tools", []))
            logger.info("Step 7 complete: Database saves finished")

            # Step 8: Generate and save resume item
            logger.info("Step 8: Generating resume item")
            resume_item = generate_resume_item(
                project_name=project_name,
                contributors=contributors,
                project_stats=project_stats,
                skill_categories=skill_report.get("skill_categories", {}),
                languages=languages,
                frameworks=frameworks,
                tools=tools_and_technologies,
                complexity_dict=complexity_dict,
                use_ai=settings.ai_resume_generation,
                api_key=settings.openai_api_key,
                ai_model=settings.ai_model,
                ai_temperature=settings.ai_temperature,
                ai_max_tokens=settings.ai_max_tokens,
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
                libraries=libraries,
                tools_and_technologies=tools_and_technologies,
                contextual_skills=contextual_skills,
                file_count=len(file_list),
                contributor_count=len(contributors),
                skill_count=self.skill_repo.count_by_project(project_id),
                library_count=self.library_repo.count_by_project(project_id),
                tool_count=self.tool_repo.count_by_project(project_id),
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
            logger.error(f"Analysis failed for {project_name}: {e}")
            raise

    def _detect_frameworks_best(self, project_path: Path) -> List[dict]:
        """Detect frameworks and return best-confidence unique list."""
        rules_path = Path(__file__).resolve().parent.parent / "core" / "rules" / "frameworks.yml"
        if not rules_path.exists():
            logger.warning("Framework rules file not found at %s", rules_path)
            return []

        results = detect_frameworks_recursive(project_path, str(rules_path))
        best: dict = {}

        for folder_frameworks in results.get("frameworks", {}).values():
            for fw in folder_frameworks:
                name = (fw.get("name") or "").strip()
                if not name:
                    continue
                conf = float(fw.get("confidence", 1.0))
                if name not in best or conf > best[name]:
                    best[name] = conf

        return [
            {"name": name, "confidence": conf}
            for name, conf in sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))
        ]

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
        # Delete old contributors for this project
        self.contributor_repo.delete_by_project_id(project_id)
        
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
                "github_username": c.get("github_username"),
                "github_email": c.get("github_email"),
                "commits": c.get("commits", 0),
                "percent": c.get("percent", 0.0),
                "total_lines_added": c.get("total_lines_added", 0),
                "total_lines_deleted": c.get("total_lines_deleted", 0),
                "files_modified": files_modified,
            })

        if contributors_data:
            self.contributor_repo.create_contributors_bulk(contributors_data)

    def _save_skills(
        self,
        project_id: int,
        skill_categories: dict,
        skill_sources: Optional[dict] = None,
    ) -> None:
        """
        Save skills to database with source tracking.

        Args:
            project_id: Project ID
            skill_categories: Dict mapping category -> list of skill names
            skill_sources: Optional dict mapping skill name -> source type
        """
        skill_sources = skill_sources or {}
        skills_data = []

        for category, skills in skill_categories.items():
            for skill in skills:
                skills_data.append({
                    "project_id": project_id,
                    "skill": skill,
                    "category": category,
                    "frequency": 1,
                    "source": skill_sources.get(skill),
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

    def _save_frameworks(self, project_id: int, frameworks: list) -> None:
        """Save detected frameworks to database."""
        if frameworks:
            self.framework_repo.create_frameworks_bulk(frameworks, project_id)
            logger.info(f"Saved {len(frameworks)} frameworks for project {project_id}")

    def _save_libraries(self, project_id: int, libraries: list) -> None:
        """Save detected libraries to database."""
        if libraries:
            self.library_repo.create_libraries_bulk(libraries, project_id)
            logger.info(f"Saved {len(libraries)} libraries for project {project_id}")

    def _save_tools(self, project_id: int, tools: list) -> None:
        """Save detected tools to database."""
        if tools:
            self.tool_repo.create_tools_bulk(tools, project_id)
            logger.info(f"Saved {len(tools)} tools for project {project_id}")

    def get_analysis_result(self, project_id: int) -> Optional[AnalysisResult]:
        """Get analysis result for a project."""
        project = self.project_repo.get(project_id)
        if not project:
            return None

        languages = self.project_repo.get_languages(project_id)
        frameworks = self.project_repo.get_frameworks(project_id)
        complexity_summary = self.complexity_repo.get_summary(project_id)
        tools_and_technologies = self.tool_repo.get_tool_names(project_id)
        contextual_skills = sorted([
            skill_obj.skill
            for skill_obj in self.skill_repo.get_skills_by_source(project_id, "contextual")
        ])

        return AnalysisResult(
            project_id=project_id,
            project_name=project.name,
            status=AnalysisStatus.COMPLETED,
            source_type=project.source_type,
            source_url=project.source_url,
            languages=languages,
            frameworks=frameworks,
            tools_and_technologies=tools_and_technologies,
            contextual_skills=contextual_skills,
            file_count=self.file_repo.count_by_project(project_id),
            contributor_count=self.contributor_repo.count_by_project(project_id),
            skill_count=self.skill_repo.count_by_project(project_id),
            library_count=self.library_repo.count_by_project(project_id),
            tool_count=self.tool_repo.count_by_project(project_id),
            total_lines_of_code=self.project_repo.get_total_lines_of_code(project_id),
            complexity_summary=ComplexitySummary(
                total_functions=complexity_summary.get("total_functions", 0),
                avg_complexity=complexity_summary.get("avg_complexity", 0.0),
                max_complexity=complexity_summary.get("max_complexity", 0),
                high_complexity_count=complexity_summary.get("high_complexity_count", 0),
            ),
            created_at=project.created_at,
        )
