"""Analysis service - main orchestration for project analysis pipeline."""

import logging
import time
import zipfile
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict
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
from src.core.analyzers.contributor import (
    analyze_contributors as git_analyze_contributors,
    get_project_creation_date,
    get_first_commit_date,
)
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


def get_earliest_file_date_from_zip(zip_path: Path) -> Optional[datetime]:
    """
    Extract the earliest file creation/modification date from a ZIP file.
    
    Reads ZIP internal metadata to find the oldest file date.
    
    Args:
        zip_path: Path to the ZIP file
        
    Returns:
        datetime object of earliest file in ZIP, or None if error
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            earliest_time = None
            
            for info in zf.infolist():
                # ZIP files store dates as (year, month, day, hour, minute, second)
                try:
                    file_time = datetime(*info.date_time)
                    
                    if earliest_time is None or file_time < earliest_time:
                        earliest_time = file_time
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error parsing date for {info.filename}: {e}")
                    continue
            
            if earliest_time:
                logger.info(f"Earliest file date in ZIP: {earliest_time}")
                return earliest_time
                
    except Exception as e:
        logger.warning(f"Error extracting file dates from ZIP: {e}")
    
    return None


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

        # Get the earliest file date from ZIP metadata
        earliest_file_date = get_earliest_file_date_from_zip(zip_path)
        logger.info(f"Earliest file date from ZIP: {earliest_file_date}")

        # Extract to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Extracting ZIP to {temp_dir}")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(temp_dir)

            # Detect actual project root with fallback strategy
            temp_path = Path(temp_dir)
            project_path = self._detect_project_root(temp_path)
            
            if project_path != temp_path:
                logger.info(f"Detected project root: {project_path.relative_to(temp_path)}")
            else:
                logger.info(f"Using extraction root as project path")

            return self._run_analysis_pipeline(
                project_path=project_path,
                project_name=name,
                source_type="zip",
                source_url=str(zip_path),
                zip_upload_time=datetime.utcnow(),
                earliest_file_date_in_zip=earliest_file_date,
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
        zip_upload_time: Optional[datetime] = None,
        earliest_file_date_in_zip: Optional[datetime] = None,
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
            zip_upload_time: Time when ZIP was uploaded (for ZIP sources)
            earliest_file_date_in_zip: Earliest file date from ZIP metadata

        Returns:
            AnalysisResult with all analysis data
        """
        logger.info(f"Starting analysis for {project_name} at {project_path}")
        
        # Track timing for performance analysis
        start_time = time.time()
        stage_timings: Dict[str, float] = {}

        try:
            # Step 0: Single-pass file collection (OPTIMIZATION)
            logger.info("Step 0: Collecting file info (single pass)")
            step_start = time.time()
            file_info_list = collect_all_file_info(project_path, show_progress=True)
            file_paths = [f.path for f in file_info_list]
            stage_timings['file_collection'] = time.time() - step_start
            logger.info(f"Step 0 complete: Collected info for {len(file_info_list)} files in {stage_timings['file_collection']:.2f}s")

            # Step 1: Convert file info to metadata format
            logger.info("Step 1: Building metadata from collected files")
            step_start = time.time()
            project_root = str(Path(project_path).resolve())
            file_list = [file_info_to_metadata_dict(f) for f in file_info_list]
            stage_timings['metadata_conversion'] = time.time() - step_start
            logger.info(f"Step 1 complete: {len(file_list)} files in {stage_timings['metadata_conversion']:.2f}s")

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
            step_start = time.time()

            # Default values in case of errors
            contributors = []
            complexity_dict = {"functions": []}
            library_report = {"libraries": [], "by_ecosystem": {}, "total_count": 0}
            tool_report = {"tools": [], "by_category": {}, "total_count": 0}
            languages_detected: List[str] = []
            frameworks_detected: List[dict] = []

            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {
                    executor.submit(git_analyze_contributors, project_root, use_all_branches=False, max_commits=None): "contributors",
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

            stage_timings['parallel_analysis'] = time.time() - step_start
            logger.info(f"Steps 3-6 complete: Parallel analysis finished in {stage_timings['parallel_analysis']:.2f}s")

            # Step 5.5: Extract skills with pre-detected signals
            logger.info("Step 5.5: Extracting skills with library/tool context")
            step_start = time.time()
            framework_names = [fw.get("name") for fw in frameworks_detected if fw.get("name")]
            skill_report = analyze_project_skills(
                project_root,
                libraries=library_report.get("libraries", []),
                tools=tool_report.get("tools", []),
                languages=languages_detected,
                frameworks=framework_names,
            )
            stage_timings['skill_extraction'] = time.time() - step_start
            logger.info("Step 5.5 complete: Found %d skills in %.2fs", skill_report.get("total_skills", 0), stage_timings['skill_extraction'])

            # Step 5.6: Cross-validate detections
            logger.info("Step 5.6: Cross-validating detections")
            step_start = time.time()
            validator = CrossValidator(
                languages=languages_detected,
                frameworks=frameworks_detected,
                libraries=library_report.get("libraries", []),
                tools=tool_report.get("tools", [])
            )
            enhanced_results = validator.get_enhanced_results()
            validation_summary = enhanced_results.validation_summary
            stage_timings['cross_validation'] = time.time() - step_start
            logger.info(
                "Step 5.6 complete: Cross-validation found %d boosted, %d gap-filled frameworks in %.2fs",
                validation_summary.get("frameworks_boosted", 0),
                validation_summary.get("gap_filled_frameworks", 0),
                stage_timings['cross_validation']
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
            step_start = time.time()
            self._save_files(project_id, file_list)
            self._save_complexity(project_id, complexity_dict.get("functions", []))
            if contributors:
                self._save_contributors(project_id, contributors)
            self._save_skills(
                project_id,
                skill_report.get("skill_categories", {}),
                skill_sources=skill_report.get("skill_sources", {}),
                skill_frequencies=skill_report.get("skill_frequencies", {}),
                file_list=file_list,
                detected_languages=languages,
                detected_frameworks=frameworks,
                project_path=project_root,
            )
            self._save_frameworks(project_id, all_enhanced_frameworks)
            self._save_libraries(project_id, library_report.get("libraries", []))
            self._save_tools(project_id, tool_report.get("tools", []))
            stage_timings['database_saves'] = time.time() - step_start
            logger.info(f"Step 7 complete: Database saves finished in {stage_timings['database_saves']:.2f}s")

            # Step 8: Generate and save resume item
            logger.info("Step 8: Generating resume item")
            step_start = time.time()
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
            stage_timings['resume_generation'] = time.time() - step_start
            logger.info(f"Step 8 complete: Resume generated in {stage_timings['resume_generation']:.2f}s")

            # Build result
            complexity_summary = self.complexity_repo.get_summary(project_id)
            
            # Calculate 4 timestamps:
            # 1. zip_uploaded_at: When ZIP was uploaded (for ZIP sources)
            # 2. first_file_created: Earliest file in ZIP (from ZIP metadata)
            # 3. first_commit_date: First Git commit (if repository)
            # 4. project_started_at: min(first_file_created, first_commit_date)
            
            # 1. zip_uploaded_at (only for ZIP sources)
            zip_uploaded_at = zip_upload_time if source_type == "zip" else datetime.utcnow()
            logger.info(f"ZIP uploaded at: {zip_uploaded_at}")
            
            # 2. first_file_created (earliest file from ZIP)
            first_file_created = earliest_file_date_in_zip if earliest_file_date_in_zip else datetime.utcnow()
            logger.info(f"First file created: {first_file_created}")
            
            # 3. first_commit_date (from Git if available)
            first_commit_date = get_first_commit_date(str(project_path))
            logger.info(f"First commit date: {first_commit_date}")
            
            # 4. project_started_at (minimum of file creation and first commit)
            if first_commit_date and first_file_created:
                project_started_at = min(first_commit_date, first_file_created)
            elif first_commit_date:
                project_started_at = first_commit_date
            else:
                project_started_at = first_file_created
            
            logger.info(f"Project started at: {project_started_at}")

            # Persist timestamps on project record for downstream consumers
            self.project_repo.update_timestamps(
                project_id=project_id,
                zip_uploaded_at=zip_uploaded_at,
                first_file_created=first_file_created,
                first_commit_date=first_commit_date,
                project_started_at=project_started_at,
            )
            
            # Step 9: Save analysis summary with timing data
            total_duration = time.time() - start_time
            self._save_analysis_summary(
                project_id=project_id,
                total_files_processed=len(file_list),
                total_files_analyzed=len([f for f in file_list if f.get('lines_of_code', 0) > 0]),
                total_files_skipped=len([f for f in file_list if f.get('lines_of_code', 0) == 0]),
                analysis_duration_seconds=total_duration,
                stage_durations=stage_timings,
            )
            logger.info(f"Analysis summary saved: Total duration {total_duration:.2f}s")
            
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
                zip_uploaded_at=zip_uploaded_at,
                first_file_created=first_file_created,
                first_commit_date=first_commit_date,
                project_started_at=project_started_at,
            )
        except Exception as e:
            logger.error(f"Analysis failed for {project_name}: {e}")
            raise

    def _detect_project_root(self, base_path: Path) -> Path:
        """
        Detect the actual project root using multiple strategies:
        1. Single subdirectory (most common ZIP structure)
        2. Directory containing .git folder (excluding __MACOSX)
        3. Fall back to base_path
        
        Args:
            base_path: Root path to search
            
        Returns:
            Path to detected project root
        """
        # Strategy 1: Check for single subdirectory (exclude __MACOSX and hidden)
        subdirs = [d for d in base_path.iterdir() 
                   if d.is_dir() and not d.name.startswith('.') and d.name != '__MACOSX']
        if len(subdirs) == 1:
            return subdirs[0]
        
        # Strategy 2: Search for .git directory (excluding __MACOSX)
        git_dirs = list(base_path.glob('**/.git'))
        # Filter out any .git directories in __MACOSX folder
        git_dirs = [gd for gd in git_dirs if '__MACOSX' not in str(gd)]
        if git_dirs:
            # Return parent of the first .git found
            project_root = git_dirs[0].parent
            logger.info(f"Found .git directory at {project_root.relative_to(base_path)}")
            return project_root
        
        # Strategy 3: Fall back to base path
        logger.debug(f"No single subdirectory or .git found, using base path")
        return base_path

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
        from datetime import datetime
        from src.models.orm.contributor_commit import ContributorCommit
        
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
                "percent": c.get("commit_percent", 0.0),  # Map commit_percent to percent (DB field)
                "total_lines_added": c.get("total_lines_added", 0),
                "total_lines_deleted": c.get("total_lines_deleted", 0),
                "files_modified": files_modified,
                "commit_dates": c.get("commit_dates", []),  # Store for later use
            })

        if contributors_data:
            created_contributors = self.contributor_repo.create_contributors_bulk(contributors_data)
            
            # Save commit history for each contributor
            for i, contributor_orm in enumerate(created_contributors):
                commit_dates = contributors_data[i].get("commit_dates", [])
                if commit_dates:
                    commit_objs = []
                    for commit_date in commit_dates:
                        if isinstance(commit_date, datetime):
                            commit_objs.append(ContributorCommit(
                                contributor_id=contributor_orm.id,
                                commit_hash="",  # Not available in current data structure
                                commit_date=commit_date,
                                author_date=commit_date,
                                commit_message="",
                            ))
                    
                    if commit_objs:
                        self.db.add_all(commit_objs)
            
            self.db.commit()

    def _save_skills(
        self,
        project_id: int,
        skill_categories: dict,
        skill_sources: Optional[dict] = None,
        skill_frequencies: Optional[dict] = None,
        file_list: Optional[List[dict]] = None,
        detected_languages: Optional[List[str]] = None,
        detected_frameworks: Optional[List[str]] = None,
        project_path: Optional[str] = None,
    ) -> None:
        """
        Save skills to database with source tracking, frequency counts, and timeline entries.

        Args:
            project_id: Project ID
            skill_categories: Dict mapping category -> list of skill names
            skill_sources: Optional dict mapping skill name -> source type
            skill_frequencies: Optional dict mapping skill name -> occurrence count
            file_list: Optional list of file metadata for timeline generation
            detected_languages: Optional list of detected language names
            detected_frameworks: Optional list of detected framework names
            project_path: Optional path to project for git history extraction
        """
        skill_sources = skill_sources or {}
        skill_frequencies = skill_frequencies or {}
        skills_data = []

        for category, skills in skill_categories.items():
            for skill in skills:
                skills_data.append({
                    "project_id": project_id,
                    "skill": skill,
                    "category": category,
                    "frequency": skill_frequencies.get(skill, 1),
                    "source": skill_sources.get(skill),
                })

        if skills_data:
            self.skill_repo.create_skills_bulk(skills_data)

        # Generate timeline entries from git history or file dates
        if file_list:
            self._save_skill_timeline(
                project_id,
                skill_categories,
                file_list,
                detected_languages=detected_languages,
                detected_frameworks=detected_frameworks,
                project_path=project_path,
            )

    def _save_skill_timeline(
        self,
        project_id: int,
        skill_categories: dict,
        file_list: List[dict],
        detected_languages: Optional[List[str]] = None,
        detected_frameworks: Optional[List[str]] = None,
        contributors: Optional[List[dict]] = None,
        project_path: Optional[str] = None,
    ) -> None:
        """
        Save skill timeline entries based on git commit history or file dates.

        Uses git commit history when available (more accurate), falls back to
        file modification timestamps otherwise. Only includes skills that are
        already in skill_categories (the meaningful, resume-worthy skills).

        Args:
            project_id: Project ID
            skill_categories: Dict mapping category -> list of skill names (from skill detector)
            file_list: List of file metadata with last_modified timestamps
            detected_languages: List of detected language names
            detected_frameworks: List of detected framework names
            contributors: List of contributor data with commit history
            project_path: Path to project for git history extraction
        """
        from collections import defaultdict

        # Only use skills from skill_categories - these are the meaningful skills
        # detected by the skill detector (not raw file formats like JSON, YAML, etc.)
        all_skills = set()
        for skills in skill_categories.values():
            all_skills.update(skills)

        if not all_skills:
            logger.info("No skills to create timeline for")
            return

        # Try to get dates from git commit history first (more accurate)
        commit_dates = self._extract_commit_dates_from_git(project_path)

        if commit_dates:
            # Use git commit dates - add all skills to the date range
            logger.info(f"Using {len(commit_dates)} git commit dates for timeline")
            min_date = min(commit_dates)
            max_date = max(commit_dates)

            timeline_data = []
            for skill in all_skills:
                # Add entry for first occurrence
                timeline_data.append({
                    "project_id": project_id,
                    "skill": skill,
                    "date": min_date,
                    "count": 1,
                })
                # Add entry for last occurrence if different
                if max_date != min_date:
                    timeline_data.append({
                        "project_id": project_id,
                        "skill": skill,
                        "date": max_date,
                        "count": 1,
                    })
        else:
            # Fall back to file modification dates
            logger.info("No git history available, using file modification dates")
            file_dates = []
            for file_meta in file_list:
                last_modified = file_meta.get("last_modified")
                if last_modified:
                    try:
                        file_date = datetime.fromtimestamp(last_modified).date()
                        file_dates.append(file_date)
                    except (ValueError, TypeError, OSError):
                        continue

            if not file_dates:
                logger.info("No file dates available for timeline")
                return

            min_date = min(file_dates)
            max_date = max(file_dates)

            timeline_data = []
            for skill in all_skills:
                timeline_data.append({
                    "project_id": project_id,
                    "skill": skill,
                    "date": min_date,
                    "count": 1,
                })
                if max_date != min_date:
                    timeline_data.append({
                        "project_id": project_id,
                        "skill": skill,
                        "date": max_date,
                        "count": 1,
                    })

        if timeline_data:
            self.skill_repo.create_timeline_bulk(timeline_data)
            logger.info(f"Saved {len(timeline_data)} skill timeline entries for project {project_id}")

    def _extract_commit_dates_from_git(self, project_path: Optional[str]) -> List:
        """
        Extract unique commit dates from git history.

        Args:
            project_path: Path to the project directory

        Returns:
            List of date objects from git commits, or empty list if not a git repo
        """
        if not project_path:
            return []

        try:
            from git import Repo, InvalidGitRepositoryError
        except ImportError:
            return []

        try:
            repo = Repo(project_path)
            commit_dates = set()

            # Get dates from recent commits (limit to avoid slow processing)
            for commit in repo.iter_commits(max_count=500):
                try:
                    commit_date = datetime.fromtimestamp(commit.committed_date).date()
                    commit_dates.add(commit_date)
                except (ValueError, TypeError, OSError):
                    continue

            return sorted(commit_dates)

        except InvalidGitRepositoryError:
            logger.debug(f"Not a git repository: {project_path}")
            return []
        except Exception as e:
            logger.debug(f"Error reading git history: {e}")
            return []

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

    def _save_analysis_summary(
        self,
        project_id: int,
        total_files_processed: int,
        total_files_analyzed: int,
        total_files_skipped: int,
        analysis_duration_seconds: float,
        stage_durations: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Save project analysis summary with timing and statistics.
        
        This function populates the ProjectAnalysisSummary table with:
        - File processing statistics (total, analyzed, skipped)
        - Total analysis duration
        - Per-stage timing breakdown for performance analysis
        
        Args:
            project_id: Project ID
            total_files_processed: Total number of files found in project
            total_files_analyzed: Number of files with content analyzed
            total_files_skipped: Number of files skipped (binary, empty, etc.)
            analysis_duration_seconds: Total analysis time in seconds
            stage_durations: Dict mapping stage name to duration in seconds
        """
        try:
            self.skill_repo.create_summary(
                project_id=project_id,
                total_files_processed=total_files_processed,
                total_files_analyzed=total_files_analyzed,
                total_files_skipped=total_files_skipped,
                analysis_duration_seconds=analysis_duration_seconds,
                stage_durations=stage_durations,
            )
            
            # Log performance insights
            if stage_durations:
                slowest_stage = max(stage_durations.items(), key=lambda x: x[1])
                logger.info(f"Performance: Slowest stage was '{slowest_stage[0]}' at {slowest_stage[1]:.2f}s")
                
        except Exception as e:
            logger.error(f"Failed to save analysis summary for project {project_id}: {e}")

    def get_analysis_result(self, project_id: int) -> Optional[AnalysisResult]:
        """Get analysis result for a project."""
        project = self.project_repo.get(project_id)
        if not project:
            return None

        languages = self.project_repo.get_languages(project_id)
        frameworks = self.project_repo.get_frameworks(project_id)
        libraries = self.project_repo.get_libraries(project_id)
        complexity_summary = self.complexity_repo.get_summary(project_id)
        tools_and_technologies = self.tool_repo.get_tool_names(project_id)
        skills = self.skill_repo.get_by_project(project_id)

        # Get stored timestamps with fallbacks
        zip_uploaded_at = project.zip_uploaded_at or project.created_at or datetime.utcnow()
        first_file_created = project.first_file_created or self.file_repo.get_earliest_file_date(project_id) or datetime.utcnow()
        first_commit_date = project.first_commit_date
        project_started_at = project.project_started_at or first_commit_date or first_file_created

        return AnalysisResult(
            project_id=project_id,
            project_name=project.name,
            status=AnalysisStatus.COMPLETED,
            source_type=project.source_type,
            source_url=project.source_url,
            languages=languages,
            frameworks=frameworks,
            libraries=libraries,
            tools_and_technologies=tools_and_technologies,
            skills=skills,
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
            zip_uploaded_at=zip_uploaded_at,
            first_file_created=first_file_created,
            first_commit_date=first_commit_date,
            project_started_at=project_started_at,
        )
