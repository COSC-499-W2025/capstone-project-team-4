"""Analysis API routes."""

import logging
import platform
import tempfile
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Optional, Union, List

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.analysis import (
    AnalysisResult,
    GitHubAnalysisRequest,
)
from src.services.analysis_service import AnalysisService
from src.api.exceptions import InvalidFileError, InvalidGitHubURLError, AnalysisError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/analyze", tags=["analysis"])


@router.post("/upload", response_model=List[AnalysisResult], status_code=201)
async def analyze_upload(
    file: UploadFile = File(..., description="ZIP file to analyze"),
    project_name: Optional[str] = Form(None, description="Custom project name"),
    create_snapshots: bool = Form(False, description="Create 2 snapshots at different time points: Mid (60%) and Late (85%) - requires git history"),
    db: Session = Depends(get_db),
):
    """
    Analyze a project from an uploaded ZIP file.

    - If create_snapshots=false (default): Analyzes the project as-is and returns 1 result
    - If create_snapshots=true: Creates 2 snapshots at different points in git history:
      - Mid (60% of commits): Midpoint of development
      - Late (85% of commits): Near the end of development

    Returns a list of analysis results (1 for regular upload, 2 for snapshots).
    """
    # Validate filename and extension
    if not file.filename:
        raise InvalidFileError("No filename provided")

    # Normalize to just the base name (some clients include paths)
    filename = Path(file.filename).name

    #  Always return list to match response_model=List[AnalysisResult]
    if filename.startswith("._") or filename == ".DS_Store":
        raise InvalidFileError(
            "macOS metadata file detected (._*). Upload the real .zip file, not the sidecar."
        )

    if not filename.lower().endswith(".zip"):
        raise InvalidFileError("File must be a ZIP archive")

    tmp_path: Optional[Path] = None
    temp_dir: Optional[tempfile.TemporaryDirectory] = None

    # Save uploaded file to temp location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            contents = await file.read()
            if not contents:
                raise InvalidFileError("Uploaded file is empty")

            tmp.write(contents)
            tmp_path = Path(tmp.name)

        service = AnalysisService(db)
        name = project_name or Path(filename).stem

        # If create_snapshots is True, create multiple snapshots
        if create_snapshots:
            temp_dir = tempfile.TemporaryDirectory()

            try:
                # Extract ZIP to check for git history
                extract_dir = Path(temp_dir.name) / "extracted"
                extract_dir.mkdir()

                with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                # Find the project directory
                project_dirs = list(extract_dir.iterdir())
                if not project_dirs:
                    raise InvalidFileError("Empty ZIP archive")

                project_path = project_dirs[0]

                # Verify .git directory exists
                git_dir = project_path / ".git"
                if not git_dir.exists():
                    raise InvalidFileError(
                        "No .git directory found. Snapshot creation requires git history. "
                        "Upload without create_snapshots=true for regular analysis."
                    )

                # Get git commit history
                # Convert path to string and use forward slashes for git on Windows
                git_project_path = str(project_path).replace("\\", "/") if platform.system() == "Windows" else str(project_path)
                result = subprocess.run(
                    ["git", "-C", git_project_path, "log", "--reverse", "--oneline", "--all"],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                commits = result.stdout.strip().split("\n")
                if not commits or not commits[0]:
                    raise InvalidFileError("No git commits found in project")

                total_commits = len(commits)

                if total_commits < 10:
                    raise InvalidFileError(
                        f"Project has only {total_commits} commits. Need at least 10 commits for snapshots. "
                        "Upload without create_snapshots=true for regular analysis."
                    )

                # Calculate snapshot points (60%, 85%)
                snapshot_points = [
                    ("Mid", int(total_commits * 0.60)),
                    ("Late", int(total_commits * 0.85)),
                ]

                # Create snapshots at each point
                analysis_results = []

                for snapshot_label, commit_index in snapshot_points:
                    commit_hash = commits[commit_index].split()[0]
                    snapshot_name = f"{name}-{snapshot_label}"

                    # Create a temporary directory for this snapshot
                    snapshot_dir = Path(temp_dir.name) / f"snapshot_{snapshot_label}"
                    snapshot_dir.mkdir()
                    snapshot_project_path = snapshot_dir / "project"

                    # Copy the entire project directory (including .git) instead of cloning
                    # Use symlinks=True on Unix, False on Windows (requires admin on Windows)
                    use_symlinks = platform.system() != "Windows"
                    shutil.copytree(project_path, snapshot_project_path, symlinks=use_symlinks)

                    # Reset to specific commit
                    git_snapshot_path = str(snapshot_project_path).replace("\\", "/") if platform.system() == "Windows" else str(snapshot_project_path)
                    subprocess.run(
                        ["git", "-C", git_snapshot_path, "reset", "--hard", commit_hash],
                        capture_output=True,
                        check=True,
                    )

                    # Clean build artifacts
                    for artifact_dir in ["node_modules", "venv", "__pycache__", ".pytest_cache", "dist", "build"]:
                        artifact_path = snapshot_project_path / artifact_dir
                        if artifact_path.exists():
                            shutil.rmtree(artifact_path, ignore_errors=True)

                    # Analyze this snapshot
                    result = service.analyze_from_directory(snapshot_project_path, snapshot_name)

                    if isinstance(result, list):
                        analysis_results.extend(result)
                    else:
                        analysis_results.append(result)

                return analysis_results

            except subprocess.CalledProcessError as e:
                raise AnalysisError(f"Git operation failed: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            finally:
                if temp_dir:
                    temp_dir.cleanup()
        else:
            # Regular single analysis
            result = service.analyze_from_zip(tmp_path, name)

            #  Always return list to match response_model=List[AnalysisResult]
            return result if isinstance(result, list) else [result]

    except (FileNotFoundError, ValueError) as e:
        # FileNotFoundError: temp file missing (rare)
        # ValueError: invalid zip, etc.
        raise InvalidFileError(str(e))
    except InvalidFileError:
        # Re-raise as-is
        raise
    except Exception as e:
        logger.exception("Analysis failed")
        raise AnalysisError(str(e))
    finally:
        # --- Clean up temp file ---
        if tmp_path:
            try:
                tmp_path.unlink(missing_ok=True)  
            except TypeError:
          
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            except Exception:
                pass


@router.post("/github", response_model=Union[AnalysisResult, List[AnalysisResult]], status_code=201)
async def analyze_github(
    request: GitHubAnalysisRequest,
    db: Session = Depends(get_db),
):
    """
    Analyze a project from a GitHub repository URL.

    - Provide a GitHub repository URL (public repos only)
    - Optionally specify a branch to analyze
    - The repository will be cloned and analyzed
    - Returns analysis results including languages, frameworks, skills, and complexity metrics
    """
    github_url = str(request.github_url)

    # Validate GitHub URL
    if "github.com" not in github_url:
        raise InvalidGitHubURLError(github_url)

    try:
        service = AnalysisService(db)
        result = service.analyze_from_github(
            github_url=github_url,
            branch=request.branch,
        )
        return result

    except ValueError as e:
        raise InvalidGitHubURLError(str(e))
    except RuntimeError as e:
        raise AnalysisError(str(e))
    except Exception as e:
        logger.error(f"GitHub analysis failed: {e}")
        raise AnalysisError(str(e))


@router.post("/directory", response_model=AnalysisResult, status_code=201)
async def analyze_directory(
    directory_path: str = Form(..., description="Path to local directory"),
    project_name: Optional[str] = Form(None, description="Custom project name"),
    db: Session = Depends(get_db),
):
    """
    Analyze a project from a local directory.

    - Provide the absolute path to a local project directory
    - Optionally specify a custom project name
    - Returns analysis results including languages, frameworks, skills, and complexity metrics

    Note: This endpoint is intended for local/development use.
    """
    path = Path(directory_path)

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")

    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {directory_path}")

    try:
        service = AnalysisService(db)
        name = project_name or path.name
        result = service.analyze_from_directory(path, name)
        return result

    except Exception as e:
        logger.error(f"Directory analysis failed: {e}")
        raise AnalysisError(str(e))
