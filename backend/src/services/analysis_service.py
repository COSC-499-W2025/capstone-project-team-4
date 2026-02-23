"""Analysis service - main orchestration for project analysis pipeline."""

import logging
import time
import zipfile
import tempfile
import shutil
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Union
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.orm.file import File
from src.models.orm.complexity import Complexity
from src.models.orm.skill import ProjectSkill, ProjectSkillTimeline
from src.models.orm.framework import ProjectFramework
from src.models.orm.library import ProjectLibrary
from src.models.orm.tool import ProjectTool
from src.models.orm.resume import ResumeItem
from src.models.orm.project import ProjectAnalysisSummary
from src.models.orm.contributor import Contributor, ContributorFile
from src.models.orm.contributor_commit import ContributorCommit

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
from src.core.utils.project_detection import detect_project_roots

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

PROJECT_MARKERS = {
    ".git",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "Cargo.toml",
    "go.mod",
    "composer.json",
    "Makefile",
}

CODE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".kt", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".php", ".rb", ".swift",
}

IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", ".next",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".idea", ".vscode",
}

logger = logging.getLogger(__name__)
logger.info("LOADED analysis_service from: %s", __file__)

def _is_macos_junk_zip_name(name: str) -> bool:
    n = name.replace("\\", "/")
    base = Path(n).name
    return (
        n.startswith("__MACOSX/") or "/__MACOSX/" in n
        or base == ".DS_Store"
        or base.startswith("._")
    )

def _extract_zip_skipping_macos_junk(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = []
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if info.is_dir():
                continue
            if _is_macos_junk_zip_name(name):
                continue
            members.append(info)
        zf.extractall(dest, members=members)

def _is_under_ignored_dir(rel_path: Union[str, Path]) -> bool:
    
    p = Path(str(rel_path).replace("\\", "/"))
    return any(part in IGNORE_DIRS for part in p.parts)

def _extract_inner_zips_recursively(root: Path, max_zip_depth: int = 2) -> None:
    """
    Finds *.zip inside extracted content and extracts them into folders next to them.
    Skips zips located under ignored dirs (e.g., .venv).
    """
    if max_zip_depth <= 0:
        return

    inner_zips = [p for p in root.rglob("*.zip") if p.is_file()]

    for z in inner_zips:
        if _is_under_ignored_dir(z):
            continue
        # skip mac junk like ._something.zip
        if _is_macos_junk_zip_name(z.name):
            continue

        extract_dir = z.with_suffix("")  # myproj.zip -> myproj/
        extract_dir.mkdir(exist_ok=True)

        try:
            _extract_zip_skipping_macos_junk(z, extract_dir)
            # optional: remove the zip so it doesn't re-trigger
            # z.unlink()
        except zipfile.BadZipFile:
            continue

    # recurse one level down
    _extract_inner_zips_recursively(root, max_zip_depth=max_zip_depth - 1)

def list_inner_zip_entries(zip_path: Path) -> list[str]:
    """
    Return a list of nested .zip entries inside zip_path.
    Skips macOS junk entries.
    """
    zip_path = Path(zip_path)
    if not zip_path.exists() or not zipfile.is_zipfile(zip_path):
        return []

    inner: list[str] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")

            # skip directories + mac junk
            if name.endswith("/") or info.is_dir():
                continue
            if _is_macos_junk_zip_name(name):
                continue

            if name.lower().endswith(".zip"):
                inner.append(name)

    return inner


def get_earliest_file_date_from_zip(zip_path: Path) -> Optional[datetime]:
    """
    Extract earliest file date from ZIP *metadata* (not filesystem).
    Skips macOS junk entries.
    """
    zip_path = Path(zip_path)

    if not zip_path.exists() or not zipfile.is_zipfile(zip_path):
        return None

    earliest: Optional[datetime] = None

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")

                # skip dirs + mac junk
                if info.is_dir() or name.endswith("/"):
                    continue
                if _is_macos_junk_zip_name(name):
                    continue

                try:
                    file_time = datetime(*info.date_time)
                except (ValueError, TypeError):
                    continue

                if earliest is None or file_time < earliest:
                    earliest = file_time

        return earliest
    except Exception:
        return None

def _extract_zip_skipping_macos_junk(zip_path: Path, dest: Path) -> None:
    """
    Extract all members except macOS junk.
    Keeps directory structure intact.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if _is_macos_junk_zip_name(name):
                continue
            zf.extract(info, dest)

def _normalize_zip_root(extracted_root: Path) -> Path:
    """
    If ZIP has exactly one visible top-level folder, treat that as the root.
    """
    children = [p for p in extracted_root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    return children[0] if len(children) == 1 else extracted_root

def _looks_like_project_root(folder: Path, min_code_files: int = 2) -> bool:
    if not folder.is_dir():
        return False
    if folder.name in IGNORE_DIRS:
        return False

    for marker in PROJECT_MARKERS:
        if (folder / marker).exists():
            return True

    # fallback: count code files
    code_count = 0
    for p in folder.rglob("*"):
        if p.is_dir() and p.name in IGNORE_DIRS:
            continue
        if p.is_file() and p.suffix.lower() in CODE_EXTS:
            code_count += 1
            if code_count >= min_code_files:
                return True

    return False


def detect_project_roots_in_zip(extracted_root: Path, max_depth: int = 4) -> list[Path]:
    """
    Detect multiple project roots inside extracted ZIP.

    - Normalize single-folder zips
    - Prefer top-level subfolders that look like projects
    - Else bounded recursive search
    """
    base = _normalize_zip_root(extracted_root)

    if _looks_like_project_root(base):
        return [base]

    top_dirs = [d for d in base.iterdir() if d.is_dir() and d.name not in IGNORE_DIRS and not d.name.startswith(".")]
    top_projects = [d for d in top_dirs if _looks_like_project_root(d)]
    if top_projects:
        return sorted(top_projects, key=lambda p: p.name.lower())

    projects: list[Path] = []

    for root, dirs, files in os.walk(base):
        root_path = Path(root)

        depth = len(root_path.resolve().relative_to(base.resolve()).parts)
        if depth > max_depth:
            dirs.clear()
            continue

        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        if _looks_like_project_root(root_path):
            projects.append(root_path)
            dirs.clear()  # don't descend into a detected project

    return sorted(projects, key=lambda p: str(p).lower()) if projects else [base]

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
        *,
        user_id: Optional[int] = None,
        _depth: int = 0,
        _max_depth: int = 5,
    ) -> List["AnalysisResult"]:
        """
        Analyze one or more projects from a ZIP.
        - Supports ZIPs inside ZIPs (recursively), but skips ones under ignored dirs
        - Skips macOS junk entries (__MACOSX, .DS_Store, ._ files)
        - Detects multiple projects per extracted zip and analyzes each root

        Returns: always List[AnalysisResult]
        """
        zip_path = Path(zip_path)

        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        if not zipfile.is_zipfile(zip_path):
            raise ValueError(f"Invalid ZIP file: {zip_path}")

        if _depth > _max_depth:
            raise ValueError("ZIP nesting too deep. Please upload fewer nested ZIP layers.")

        base_name = project_name or zip_path.stem
    
        earliest_file_date = get_earliest_file_date_from_zip(zip_path)

        results: List["AnalysisResult"] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            logger.info(f"[zip depth={_depth}] Extracting ZIP to {temp_path}")
            _extract_zip_skipping_macos_junk(zip_path, temp_path)

            inner_zip_entries = list_inner_zip_entries(zip_path)
            for inner_name in sorted(inner_zip_entries):
                inner_zip_path = temp_path / inner_name
                if not inner_zip_path.exists():
                    logger.warning(f"Inner zip listed but not extracted: {inner_name}")
                    continue

                nested_name = f"{base_name} - {Path(inner_name).stem}"
                results.extend(
                    self.analyze_from_zip(
                        inner_zip_path,
                        nested_name,
                        user_id=user_id,
                        _depth=_depth + 1,
                        _max_depth=_max_depth,
                    )
                )

            # 2) analyze project roots in the extracted content
            project_roots = detect_project_roots(temp_path)
            logger.info(f"Detected {len(project_roots)} project(s) in extracted ZIP at depth {_depth}")

            for idx, root in enumerate(project_roots, start=1):
                rel = str(root.resolve().relative_to(temp_path.resolve())).replace("\\", "/")
                if _is_under_ignored_dir(rel):
                    continue

                derived_name = base_name if len(project_roots) == 1 else f"{base_name} - {root.name or f'project-{idx}'}"

                result = self._run_analysis_pipeline(
                    project_path=root,
                    project_name=derived_name,
                    source_type="zip",
                    source_url=str(zip_path),
                    user_id=user_id,
                    zip_upload_time=datetime.utcnow(),
                    earliest_file_date_in_zip=earliest_file_date,
                )
                results.append(result)

        return results

    
    def analyze_from_directory(
        self,
        directory_path: Path,
        project_name: Optional[str] = None,
        user_id: Optional[int] = None,
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
            user_id=user_id,
        )
    
    def _compute_project_tree_hash(files_meta: list[dict]) -> str:
        h = hashlib.sha256()

        items: list[tuple[str, str]] = []
        for m in files_meta:
            path = (m.get("path") or "").replace("\\", "/")
            content_hash = m.get("content_hash") or ""
            items.append((path, content_hash))

        items.sort(key=lambda x: x[0])

        for path, content_hash in items:
            h.update(path.encode("utf-8"))
            h.update(b"\0")
            h.update(content_hash.encode("utf-8"))
            h.update(b"\n")

        return h.hexdigest()


    def _compute_analysis_key(project_hash: str, version: str) -> str:
        return hashlib.sha256(f"{project_hash}:{version}".encode("utf-8")).hexdigest()


    def analyze_from_github(
        self,
        github_url: str,
        branch: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> List[AnalysisResult]:
        """
        Analyze one or more projects from a GitHub repository.
        Supports monorepos / multi-project repositories.
        """

        from src.core.utils.project_detection import detect_project_roots, IGNORE_DIRS

        # Parse GitHub URL
        parsed = urlparse(github_url)
        if "github.com" not in parsed.netloc:
            raise ValueError(f"Invalid GitHub URL: {github_url}")

        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL format: {github_url}")

        owner, repo = path_parts[0], path_parts[1].replace(".git", "")
        project_name = repo

        with tempfile.TemporaryDirectory() as temp_dir:
            clone_path = Path(temp_dir) / repo
            clone_url = f"https://github.com/{owner}/{repo}.git"

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

            # Detect projects inside the repo
            project_roots = detect_project_roots(clone_path)

            logger.info(f"Detected {len(project_roots)} project(s) in GitHub repo")

            results: List[AnalysisResult] = []

            for root in project_roots:
                name = root.name if root != clone_path else project_name

                result = self._run_analysis_pipeline(
                    project_path=root,
                    project_name=name,
                    source_type="github",
                    source_url=github_url,
                    user_id=user_id,
                )
                results.append(result)

            return results

    def _run_analysis_pipeline(
        self,
        project_path: Path,
        project_name: str,
        source_type: str,
        source_url: Optional[str] = None,
        user_id: Optional[int] = None,
        zip_upload_time: Optional[datetime] = None,
        earliest_file_date_in_zip: Optional[datetime] = None,
    ) -> AnalysisResult:
        """
        Run the full analysis pipeline on a project.

        This optimized pipeline:
        1. Collects all file info in a SINGLE pass (avoiding redundant walks)
        2. Runs Git, Complexity, and Skill analysis in PARALLEL
        """
        # Step 0: Single-pass file collection
        logger.info("Step 0: Collecting file info (single pass)")
        start_time = time.time()
        stage_timings: Dict[str, float] = {}
        step_start = time.time()

        file_info_list = collect_all_file_info(project_path, show_progress=True)
        original_count = len(file_info_list)

        def _sha256_file(path: str, chunk_size: int = 1024 * 1024) -> str:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    h.update(chunk)
            return h.hexdigest()

        seen_hashes: set[str] = set()
        deduped_file_info: List[FileInfo] = []
        hash_by_path: Dict[str, str] = {}

        for fi in file_info_list:
            try:
                digest = _sha256_file(fi.path)
                hash_by_path[fi.relative_path] = digest
            except Exception:
                
                deduped_file_info.append(fi)
                continue

            if digest in seen_hashes:
                continue

            seen_hashes.add(digest)
            deduped_file_info.append(fi)

        file_info_list = deduped_file_info
        file_paths = [f.path for f in file_info_list]

        stage_timings["file_collection"] = time.time() - step_start
        logger.info(
            "Step 0 complete: Collected %d files, deduped to %d files in %.2fs",
            original_count,
            len(file_info_list),
            stage_timings["file_collection"],
        )

        # Step 1: Convert file info to metadata format
        logger.info("Step 1: Building metadata from collected files")
        step_start = time.time()

        project_root = str(Path(project_path).resolve())
        file_list = [file_info_to_metadata_dict(f) for f in file_info_list]

        
        for meta in file_list:
            p = meta.get("path")
            if p and p in hash_by_path:
                meta["content_hash"] = hash_by_path[p]
            else:
                meta["content_hash"] = None

        logger.info(
            "[CACHE] about to hash: files=%d with_hash=%d",
            len(file_list),
            sum(1 for f in file_list if f.get("content_hash")),
        )

        stage_timings["metadata_conversion"] = time.time() - step_start
        logger.info(
            "Step 1 complete: %d files in %.2fs",
            len(file_list),
            stage_timings["metadata_conversion"],
        )

        # Step 1.5: Compute project hash + cache lookup
        logger.info("Step 1.5: Computing project hash + cache lookup")
        step_start = time.time()

        def _compute_project_tree_hash(files_meta: list[dict]) -> str:
            """
            Stable hash of the project content:
            hash over sorted (relative_path + '\\0' + file_content_hash + '\\n')
            """
            h = hashlib.sha256()
            items: list[tuple[str, str]] = []
            for m in files_meta:
                path = (m.get("path") or "").replace("\\", "/")
                ch = m.get("content_hash") or ""
                items.append((path, ch))

            items.sort(key=lambda x: x[0])

            for path, ch in items:
                h.update(path.encode("utf-8"))
                h.update(b"\0")
                h.update(ch.encode("utf-8"))
                h.update(b"\n")

            return h.hexdigest()

        project_tree_hash = _compute_project_tree_hash(file_list)
        analysis_key = hashlib.sha256(
            f"{project_tree_hash}:{settings.app_version}".encode("utf-8")
        ).hexdigest()

        logger.info(
            "[CACHE] project_tree_hash=%s analysis_key=%s",
            project_tree_hash,
            analysis_key,
        )

        cached_project = None
        if settings.skip_analysis_cache:
            logger.info("Cache bypass enabled via SKIP_ANALYSIS_CACHE")
        else:
            cached_project = self.project_repo.get_latest_by_analysis_key(analysis_key)

        stage_timings["cache_lookup"] = time.time() - step_start
        if cached_project:
            logger.info(
                "Cache HIT: analysis_key=%s (cached project_id=%s)",
                analysis_key,
                cached_project.id,
            )
        else:
            logger.info("Cache MISS: analysis_key=%s", analysis_key)

        # Step 2: Create project entry (ALWAYS new project_id)
        logger.info("Step 2: Creating project entry")
        logger.info(f"project_tree_hash={project_tree_hash} analysis_key={analysis_key}")
        project = self.project_repo.create_project(
            name=project_name,
            root_path=project_root,
            user_id=user_id,
            source_type=source_type,
            source_url=source_url,
            content_hash=project_tree_hash,
            analysis_key=analysis_key,
            reused_from_project_id=cached_project.id if cached_project else None,
        )
        project_id = project.id
        logger.info(f"Step 2 complete: Project ID {project_id}")

        
        if cached_project is not None:
            logger.info(
                "Reusing cached analysis from project_id=%s -> new project_id=%s",
                cached_project.id,
                project_id,
            )
            self._clone_project_analysis(
                from_project_id=cached_project.id,
                to_project_id=project_id,
            )

            # Keep timestamps logic consistent (optional but recommended)
            zip_uploaded_at = zip_upload_time if source_type == "zip" else datetime.utcnow()
            first_file_created = earliest_file_date_in_zip if earliest_file_date_in_zip else datetime.utcnow()
            first_commit_date = get_first_commit_date(str(project_path))

            if first_commit_date and first_file_created:
                project_started_at = min(first_commit_date, first_file_created)
            elif first_commit_date:
                project_started_at = first_commit_date
            else:
                project_started_at = first_file_created

            self.project_repo.update_timestamps(
                project_id=project_id,
                zip_uploaded_at=zip_uploaded_at,
                first_file_created=first_file_created,
                first_commit_date=first_commit_date,
                project_started_at=project_started_at,
            )

           
            return self.get_analysis_result(project_id)
        
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
            task_start_times = {}  # Track start time for each task
            futures = {}
            
            # Submit all tasks and record their start times
            task_configs = [
                ("contributors", git_analyze_contributors, project_root),
                ("complexity", lambda: project_analysis_to_dict(analyze_project(project_path, file_paths)), None),
                ("languages", lambda: ProjectAnalyzer().analyze_project_languages(project_root), None),
            ]
            
            # Conditionally add library and tool detection
            if settings.enable_library_tool_detection:
                task_configs.extend([
                    ("libraries", detect_libraries_recursive, project_path),
                    ("tools", detect_tools_recursive, project_path),
                ])
            
            # Conditionally add framework detection
            if settings.enable_framework_detection:
                task_configs.append(
                    ("frameworks", self._detect_frameworks_best, project_path)
                )
            
            for task_name, task_func, arg in task_configs:
                task_start_times[task_name] = time.time()
                if arg is not None:
                    future = executor.submit(task_func, arg)
                else:
                    future = executor.submit(task_func)
                futures[future] = task_name

            for future in as_completed(futures):
                task_name = futures[future]
                elapsed = time.time() - task_start_times[task_name]
                try:
                    result = future.result()
                    if task_name == "contributors":
                        contributors = result
                        logger.info("Git analysis complete: Found %d contributors in %.2fs", len(contributors), elapsed)
                    elif task_name == "complexity":
                        complexity_dict = result
                        logger.info(
                            "Complexity analysis complete: Found %d functions in %.2fs",
                            len(complexity_dict.get("functions", [])),
                            elapsed,
                        )
                    elif task_name == "libraries":
                        library_report = result
                        logger.info(
                            "Library detection complete: Found %d libraries in %.2fs",
                            library_report.get("total_count", 0),
                            elapsed,
                        )
                    elif task_name == "tools":
                        tool_report = result
                        logger.info(
                            "Tool detection complete: Found %d tools in %.2fs",
                            tool_report.get("total_count", 0),
                            elapsed,
                        )
                    elif task_name == "languages":
                        languages_detected = sorted(
                            [lang for lang, count in result.items() if lang != "Unknown" and count > 0]
                        )
                        logger.info("Language detection complete: Found %d languages in %.2fs", len(languages_detected), elapsed)
                    elif task_name == "frameworks":
                        frameworks_detected = result or []
                        logger.info("Framework detection complete: Found %d frameworks in %.2fs", len(frameworks_detected), elapsed)
                except Exception as e:
                    logger.warning("%s analysis failed in %.2fs: %s", task_name, elapsed, e)

        stage_timings["parallel_analysis"] = time.time() - step_start
        logger.info(
            "Steps 3-6 complete: Parallel analysis finished in %.2fs",
            stage_timings["parallel_analysis"],
        )


        try:
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
            stage_timings["skill_extraction"] = time.time() - step_start
            logger.info(
                "Step 5.5 complete: Found %d skills in %.2fs",
                skill_report.get("total_skills", 0),
                stage_timings["skill_extraction"],
            )

            # Step 5.6: Cross-validate detections
            logger.info("Step 5.6: Cross-validating detections")
            step_start = time.time()
            validator = CrossValidator(
                languages=languages_detected,
                frameworks=frameworks_detected,
                libraries=library_report.get("libraries", []),
                tools=tool_report.get("tools", []),
            )
            enhanced_results = validator.get_enhanced_results()
            validation_summary = enhanced_results.validation_summary
            stage_timings["cross_validation"] = time.time() - step_start
            logger.info(
                "Step 5.6 complete: Cross-validation found %d boosted, %d gap-filled frameworks in %.2fs",
                validation_summary.get("frameworks_boosted", 0),
                validation_summary.get("gap_filled_frameworks", 0),
                stage_timings["cross_validation"],
            )

            # Merge enhanced frameworks with gap-filled ones
            all_enhanced_frameworks = enhanced_results.get_all_frameworks()

            # Step 6: Calculate project stats (uses contributors from parallel analysis)
            logger.info("Step 6: Calculating project stats")
            project_stats = calculate_project_stats(project_root, file_list, contributors)
            logger.info("Step 6 complete")

            languages = sorted(set(languages_detected))
            frameworks = sorted(
                set(fw.get("name", "") for fw in all_enhanced_frameworks if fw.get("name"))
            )
            libraries = sorted(
                {lib.get("name", "").strip() for lib in library_report.get("libraries", []) if lib.get("name")}
            )
            tools_and_technologies = sorted(
                {tool.get("name", "").strip() for tool in tool_report.get("tools", []) if tool.get("name")}
            )
            contextual_skills = sorted(
                [
                    skill
                    for skill, source in skill_report.get("skill_sources", {}).items()
                    if source == "contextual"
                ]
            )

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
            stage_timings["database_saves"] = time.time() - step_start
            logger.info(
                "Step 7 complete: Database saves finished in %.2fs",
                stage_timings["database_saves"],
            )

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
            stage_timings["resume_generation"] = time.time() - step_start
            logger.info(
                "Step 8 complete: Resume generated in %.2fs",
                stage_timings["resume_generation"],
            )

            # Build result
            complexity_summary = self.complexity_repo.get_summary(project_id)

            zip_uploaded_at = zip_upload_time if source_type == "zip" else datetime.utcnow()
            first_file_created = earliest_file_date_in_zip if earliest_file_date_in_zip else datetime.utcnow()
            first_commit_date = get_first_commit_date(str(project_path))

            if first_commit_date and first_file_created:
                project_started_at = min(first_commit_date, first_file_created)
            elif first_commit_date:
                project_started_at = first_commit_date
            else:
                project_started_at = first_file_created

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
                total_files_analyzed=len([f for f in file_list if f.get("lines_of_code", 0) > 0]),
                total_files_skipped=len([f for f in file_list if f.get("lines_of_code", 0) == 0]),
                analysis_duration_seconds=total_duration,
                stage_durations=stage_timings,
            )

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

    def _clone_project_analysis(self, from_project_id: int, to_project_id: int) -> None:
        """
        Copy analysis outputs from one project to another.
        Assumes the destination project row already exists.
        """
        try:
            # Files 
            src_files = list(
                self.db.scalars(select(File).where(File.project_id == from_project_id)).all()
            )
            new_files = [
                File(
                    project_id=to_project_id,
                    path=f.path,
                    language_id=f.language_id,
                    file_size=f.file_size,
                    lines_of_code=f.lines_of_code,
                    comment_lines=f.comment_lines,
                    blank_lines=f.blank_lines,
                    created_timestamp=f.created_timestamp,
                    last_modified=f.last_modified,
                    content_hash=getattr(f, "content_hash", None),
                )
                for f in src_files
            ]
            self.db.add_all(new_files)

            # Complexity
            src_cx = list(
                self.db.scalars(select(Complexity).where(Complexity.project_id == from_project_id)).all()
            )
            self.db.add_all(
                [
                    Complexity(
                        project_id=to_project_id,
                        file_path=c.file_path,
                        function_name=c.function_name,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        cyclomatic_complexity=c.cyclomatic_complexity,
                    )
                    for c in src_cx
                ]
            )

            # Skills 
            src_skills = list(
                self.db.scalars(select(ProjectSkill).where(ProjectSkill.project_id == from_project_id)).all()
            )
            self.db.add_all(
                [
                    ProjectSkill(
                        project_id=to_project_id,
                        skill_id=s.skill_id,
                        frequency=s.frequency,
                        source=s.source,
                    )
                    for s in src_skills
                ]
            )

            # Skill timeline
            src_tl = list(
                self.db.scalars(
                    select(ProjectSkillTimeline).where(ProjectSkillTimeline.project_id == from_project_id)
                ).all()
            )
            self.db.add_all(
                [
                    ProjectSkillTimeline(
                        project_id=to_project_id,
                        skill=t.skill,
                        date=t.date,
                        count=t.count,
                    )
                    for t in src_tl
                ]
            )

            #Frameworks / Libraries / Tools
            src_fw = list(
                self.db.scalars(select(ProjectFramework).where(ProjectFramework.project_id == from_project_id)).all()
            )
            self.db.add_all(
                [
                    ProjectFramework(
                        project_id=to_project_id,
                        framework_id=f.framework_id,
                        detection_score=f.detection_score,
                        original_score=f.original_score,
                        cross_validation_boost=f.cross_validation_boost,
                        validation_sources=f.validation_sources,
                        is_gap_filled=f.is_gap_filled,
                    )
                    for f in src_fw
                ]
            )

            src_lib = list(
                self.db.scalars(select(ProjectLibrary).where(ProjectLibrary.project_id == from_project_id)).all()
            )
            self.db.add_all(
                [
                    ProjectLibrary(
                        project_id=to_project_id,
                        library_id=l.library_id,
                        detection_score=l.detection_score,
                    )
                    for l in src_lib
                ]
            )

            src_tools = list(
                self.db.scalars(select(ProjectTool).where(ProjectTool.project_id == from_project_id)).all()
            )
            self.db.add_all(
                [
                    ProjectTool(
                        project_id=to_project_id,
                        tool_id=t.tool_id,
                        detection_score=t.detection_score,
                    )
                    for t in src_tools
                ]
            )

            #Resume items
            src_resume = list(
                self.db.scalars(select(ResumeItem).where(ResumeItem.project_id == from_project_id)).all()
            )
            self.db.add_all(
                [
                    ResumeItem(
                        project_id=to_project_id,
                        title=r.title,
                        highlights=r.highlights,
                        created_at=r.created_at,
                    )
                    for r in src_resume
                ]
            )

            #Analysis summary 
            src_summary = self.db.scalar(
                select(ProjectAnalysisSummary).where(ProjectAnalysisSummary.project_id == from_project_id)
            )
            if src_summary:
                self.db.add(
                    ProjectAnalysisSummary(
                        project_id=to_project_id,
                        total_files_processed=src_summary.total_files_processed,
                        total_files_analyzed=src_summary.total_files_analyzed,
                        total_files_skipped=src_summary.total_files_skipped,
                        analysis_duration_seconds=src_summary.analysis_duration_seconds,
                        analysis_stage_durations=src_summary.analysis_stage_durations,
                    )
                )

            #Contributors
            src_contribs = list(
                self.db.scalars(select(Contributor).where(Contributor.project_id == from_project_id)).all()
            )

            old_to_new_contrib_id: dict[int, int] = {}

            for c in src_contribs:
                new_c = Contributor(
                    project_id=to_project_id,
                    name=c.name,
                    email=c.email,
                    github_username=c.github_username,
                    github_email=c.github_email,
                    commits=c.commits,
                    percent=c.percent,
                    total_lines_added=c.total_lines_added,
                    total_lines_deleted=c.total_lines_deleted,
                )
                self.db.add(new_c)
                self.db.flush()  # assigns new_c.id
                old_to_new_contrib_id[c.id] = new_c.id

                # contributor_files
                src_cfiles = list(
                    self.db.scalars(select(ContributorFile).where(ContributorFile.contributor_id == c.id)).all()
                )
                self.db.add_all(
                    [
                        ContributorFile(
                            contributor_id=new_c.id,
                            filename=cf.filename,
                            modifications=cf.modifications,
                        )
                        for cf in src_cfiles
                    ]
                )

                # contributor_commits
                src_commits = list(
                    self.db.scalars(select(ContributorCommit).where(ContributorCommit.contributor_id == c.id)).all()
                )
                self.db.add_all(
                    [
                        ContributorCommit(
                            contributor_id=new_c.id,
                            commit_hash=cc.commit_hash,
                            commit_date=cc.commit_date,
                            author_date=cc.author_date,
                            commit_message=cc.commit_message,
                        )
                        for cc in src_commits
                    ]
                )

            self.db.commit()

        except Exception:
            self.db.rollback()
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
            logger.info(f"Found .git directory at {project_root.resolve().relative_to(base_path.resolve())}")
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
        """
        Save file metadata to database.

        Defensive: only pass known columns to the repository.
        Now includes content_hash (column exists in DB).
        """

        allowed_keys = {
            "project_id",
            "path",
            "language_name",
            "file_size",
            "lines_of_code",
            "comment_lines",
            "blank_lines",
            "created_timestamp",
            "last_modified",
            "content_hash",
        }

        files_data = []

        for f in file_list:
            row = {
                "project_id": project_id,
                "path": f.get("path", ""),
                "language_name": f.get("language"),
                "file_size": f.get("file_size"),
                "lines_of_code": f.get("lines_of_code"),
                "comment_lines": f.get("comment_lines"),
                "blank_lines": f.get("blank_lines"),
                "created_timestamp": f.get("created_timestamp"),
                "last_modified": f.get("last_modified"),
                "content_hash": f.get("content_hash"),
            }

            # Filter strictly to DB columns
            row = {k: v for k, v in row.items() if k in allowed_keys}
            files_data.append(row)

        if files_data:
            self.file_repo.create_files_bulk(files_data)

    def _save_complexity(self, project_id: int, functions: list[dict]) -> None:
        
        if not functions:
            return

        complexity_data = []
        for fn in functions:
            complexity_data.append({
                "project_id": project_id,                    
                "file_path": fn.get("file_path") or fn.get("file") or "",
                "function_name": fn.get("name") or fn.get("function_name") or "",
                "start_line": fn.get("start_line"),
                "end_line": fn.get("end_line"),
                "cyclomatic_complexity": fn.get("complexity") or fn.get("cyclomatic_complexity") or 0,
        })

        self.complexity_repo.create_complexities_bulk(project_id, complexity_data)

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

    def _resolve_deferred_analysis_path(
        self,
        project_path: str,
        source_url: Optional[str] = None,
    ) -> Tuple[Path, Optional[tempfile.TemporaryDirectory]]:
        """Resolve a usable project path for deferred analyses.

        If the stored project path no longer exists (e.g., temp extraction path),
        try to rehydrate from the persisted source ZIP.
        """
        project_root = Path(project_path)
        if project_root.exists():
            return project_root, None

        if source_url:
            source_path = Path(source_url)
            if source_path.exists() and source_path.suffix.lower() == ".zip" and zipfile.is_zipfile(source_path):
                temp_dir = tempfile.TemporaryDirectory()
                extract_root = Path(temp_dir.name)

                _extract_zip_skipping_macos_junk(source_path, extract_root)
                _extract_inner_zips_recursively(extract_root, max_zip_depth=2)

                roots = detect_project_roots_in_zip(extract_root)
                return (roots[0] if roots else extract_root), temp_dir

        raise FileNotFoundError(
            f"Project path not found for deferred analysis: {project_path}. "
            "Upload source may be unavailable."
        )

    def analyze_libraries_and_tools(
        self,
        project_id: int,
        project_path: str,
        source_url: Optional[str] = None,
    ) -> dict:
        """
        Analyze libraries and tools for an existing project.
        Updates the database with detected libraries and tools.
        """
        logger.info("Starting library and tool analysis for project %d", project_id)
        start_time = time.time()
        project_root, temp_dir = self._resolve_deferred_analysis_path(project_path, source_url)
        
        try:
            # Delete existing libraries and tools
            self.library_repo.delete_by_project(project_id)
            self.tool_repo.delete_by_project(project_id)

            # Run analyses
            library_report = detect_libraries_recursive(project_root)
            tool_report = detect_tools_recursive(project_root)

            # Save to database
            if library_report.get("libraries"):
                self.library_repo.create_libraries_bulk(library_report["libraries"], project_id)
            if tool_report.get("tools"):
                self.tool_repo.create_tools_bulk(tool_report["tools"], project_id)

            tool_names = sorted(
                {
                    tool.get("name", "").strip()
                    for tool in tool_report.get("tools", [])
                    if tool.get("name")
                }
            )
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()
        
        elapsed = time.time() - start_time
        logger.info(
            "Library and tool analysis complete for project %d: %d libraries, %d tools in %.2fs",
            project_id,
            library_report.get("total_count", 0),
            tool_report.get("total_count", 0),
            elapsed,
        )
        
        return {
            "project_id": project_id,
            "libraries_found": library_report.get("total_count", 0),
            "tools_found": tool_report.get("total_count", 0),
            "tools": tool_names,
            "duration_seconds": elapsed,
        }

    def analyze_frameworks(
        self,
        project_id: int,
        project_path: str,
        source_url: Optional[str] = None,
    ) -> dict:
        """
        Analyze frameworks for an existing project.
        Updates the database with detected frameworks.
        """
        logger.info("Starting framework analysis for project %d", project_id)
        start_time = time.time()
        project_root, temp_dir = self._resolve_deferred_analysis_path(project_path, source_url)
        
        try:
            # Delete existing frameworks
            self.framework_repo.delete_by_project(project_id)

            # Run framework detection
            frameworks_detected = self._detect_frameworks_best(project_root)

            # Save to database
            if frameworks_detected:
                self.framework_repo.create_frameworks_bulk(frameworks_detected, project_id)

            framework_names = sorted(
                {
                    framework.get("name", "").strip()
                    for framework in frameworks_detected
                    if framework.get("name")
                }
            )
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()
        
        elapsed = time.time() - start_time
        logger.info(
            "Framework analysis complete for project %d: %d frameworks in %.2fs",
            project_id,
            len(frameworks_detected) if frameworks_detected else 0,
            elapsed,
        )
        
        return {
            "project_id": project_id,
            "frameworks_found": len(frameworks_detected) if frameworks_detected else 0,
            "frameworks": framework_names,
            "duration_seconds": elapsed,
        }

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
