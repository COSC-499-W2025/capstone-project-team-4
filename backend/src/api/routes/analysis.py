"""Analysis API routes."""

import logging
import uuid
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
from src.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/analyze", tags=["analysis"])


@router.post("/upload", response_model=List[AnalysisResult], status_code=201)
async def analyze_upload(
    file: UploadFile = File(..., description="ZIP file to analyze"),
    project_name: Optional[str] = Form(None, description="Custom project name"),
    reuse_cached_analysis: bool = Form(
        True,
        description="If true, reuse previous analysis when the same project content is uploaded again.",
    ),
    split_projects: bool = Form(False, description="If true, split upload into multiple projects"),
    db: Session = Depends(get_db),
):
    logger.info(
        "Received upload request - filename=%s content_type=%s project_name=%s reuse_cached_analysis=%s split_projects=%s",
        file.filename,
        file.content_type,
        project_name,
        reuse_cached_analysis,
        split_projects,
    )

    # Validate filename and extension
    if not file.filename:
        logger.error("No filename provided in upload request")
        raise InvalidFileError("No filename provided")

    # Normalize to just the base name (some clients include paths)
    filename = Path(file.filename).name
    logger.info("Normalized filename: %s", filename)

    # Reject macOS metadata files
    if filename.startswith("._") or filename == ".DS_Store":
        logger.error("macOS metadata file detected: %s", filename)
        raise InvalidFileError(
            "macOS metadata file detected (._*). Upload the real .zip file, not the sidecar."
        )

    if not filename.lower().endswith(".zip"):
        logger.error("File does not end with .zip: %s", filename)
        raise InvalidFileError("File must be a ZIP archive")

    tmp_path: Path | None = None

    try:
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        saved_name = f"{uuid.uuid4().hex}_{filename}"
        tmp_path = settings.uploads_dir / saved_name

        contents = await file.read()
        logger.info("Read %s bytes from uploaded file", len(contents))

        if not contents:
            logger.error("Uploaded file is empty")
            raise InvalidFileError("Uploaded file is empty")

        tmp_path.write_bytes(contents)
        logger.info("Saved uploaded ZIP to path: %s", tmp_path)

        # Run analysis
        service = AnalysisService(db)
        name = project_name or Path(filename).stem
        logger.info("Starting analysis for project: %s", name)

        result = service.analyze_from_zip(
            tmp_path,
            name,
            use_cache=reuse_cached_analysis,
            split_projects=split_projects,  # ✅ pass through
        )

        # Always return list to match response_model=List[AnalysisResult]
        final_result = result if isinstance(result, list) else [result]
        logger.info("Analysis completed successfully, returning %s project(s)", len(final_result))
        return final_result

    except (FileNotFoundError, ValueError) as e:
        logger.error("File or value error during analysis: %s", str(e))
        raise InvalidFileError(str(e))
    except InvalidFileError:
        raise
    except Exception as e:
        logger.exception("Analysis failed with unexpected error")
        raise AnalysisError(str(e))
    finally:
        if tmp_path is not None:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
                    logger.info("Deleted uploaded ZIP after analysis: %s", tmp_path)
            except Exception as e:
                logger.warning("Failed to delete uploaded ZIP %s: %s", tmp_path, e)


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