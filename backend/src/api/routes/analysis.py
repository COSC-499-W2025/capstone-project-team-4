"""Analysis API routes."""

import logging
import subprocess
import tempfile
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
from src.services.snapshot_analysis_service import SnapshotAnalysisService
from src.api.exceptions import InvalidFileError, InvalidGitHubURLError, AnalysisError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/analyze", tags=["analysis"])


@router.post("/upload", response_model=List[AnalysisResult], status_code=201)
async def analyze_upload(
    file: UploadFile = File(..., description="ZIP file to analyze"),
    project_name: Optional[str] = Form(None, description="Custom project name"),
    create_snapshots: bool = Form(False, description="Create 2 snapshots: Old (50% of history) and Current (uploaded version) - requires git history"),
    db: Session = Depends(get_db),
):
    """
    Analyze a project from an uploaded ZIP file.

    - If create_snapshots=false (default): Analyzes the project as-is and returns 1 result
    - If create_snapshots=true: Creates 2 snapshots:
      - Old (50% of commits): Midpoint of development
      - Current (100%): The uploaded version (latest state)

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

        name = project_name or Path(filename).stem

        # If create_snapshots is True, create multiple snapshots
        if create_snapshots:
            try:
                # Delegate to SnapshotAnalysisService for snapshot workflow
                snapshot_service = SnapshotAnalysisService(db)
                return snapshot_service.analyze_with_snapshots(tmp_path, name)
            except ValueError as e:
                # Convert ValueError from validation to InvalidFileError
                raise InvalidFileError(
                    f"{str(e)} Upload without create_snapshots=true for regular analysis."
                )
            except (RuntimeError, subprocess.CalledProcessError) as e:
                # RuntimeError from git operations, CalledProcessError from subprocess
                raise InvalidFileError(
                    f"Git operation failed: {str(e)}. Upload without create_snapshots=true for regular analysis."
                )
        else:
            # Regular single analysis
            service = AnalysisService(db)
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
