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
    db: Session = Depends(get_db),
):
    # Log incoming request details
    logger.info(f"Received upload request - filename: {file.filename}, content_type: {file.content_type}, project_name: {project_name}")

    # Validate filename and extension
    if not file.filename:
        logger.error("No filename provided in upload request")
        raise InvalidFileError("No filename provided")

    # Normalize to just the base name (some clients include paths)
    filename = Path(file.filename).name
    logger.info(f"Normalized filename: {filename}")

    #  Always return list to match response_model=List[AnalysisResult]
    if filename.startswith("._") or filename == ".DS_Store":
        logger.error(f"macOS metadata file detected: {filename}")
        raise InvalidFileError(
            "macOS metadata file detected (._*). Upload the real .zip file, not the sidecar."
        )

    if not filename.lower().endswith(".zip"):
        logger.error(f"File does not end with .zip: {filename}")
        raise InvalidFileError("File must be a ZIP archive")

    # Save uploaded file to persistent location
    try:
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        saved_name = f"{uuid.uuid4().hex}_{filename}"
        tmp_path = settings.uploads_dir / saved_name
        with tmp_path.open("wb") as tmp:
            contents = await file.read()
            logger.info(f"Read {len(contents)} bytes from uploaded file")

            if not contents:
                logger.error("Uploaded file is empty")
                raise InvalidFileError("Uploaded file is empty")

            tmp.write(contents)
            logger.info(f"Saved uploaded ZIP to persistent path: {tmp_path}")

        # Run analysis
        service = AnalysisService(db)
        name = project_name or Path(filename).stem
        logger.info(f"Starting analysis for project: {name}")
        result = service.analyze_from_zip(tmp_path, name)

        #  Always return list to match response_model=List[AnalysisResult]
        final_result = result if isinstance(result, list) else [result]
        logger.info(f"Analysis completed successfully, returning {len(final_result)} project(s)")
        return final_result

    except (FileNotFoundError, ValueError) as e:
        # FileNotFoundError: temp file missing (rare)
        # ValueError: invalid zip, etc.
        logger.error(f"File or value error during analysis: {str(e)}")
        raise InvalidFileError(str(e))
    except InvalidFileError:
        # Re-raise as-is (already logged above)
        raise
    except Exception as e:
        logger.exception("Analysis failed with unexpected error")
        raise AnalysisError(str(e))


@router.post("/{project_id}/analyze-libraries-tools", status_code=200)
def analyze_project_libraries_tools(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Analyze libraries and tools for an existing project.
    This can be called after upload to run detailed detection.
    """
    logger.info(f"Received request to analyze libraries/tools for project: {project_id}")
    
    service = AnalysisService(db)
    project = service.project_repo.get(project_id)
    
    if not project:
        logger.error(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    try:
        result = service.analyze_libraries_and_tools(project_id, project.root_path, project.source_url)
        logger.info(f"Library/tool analysis completed for project {project_id}")
        return result
    except Exception as e:
        logger.exception(f"Library/tool analysis failed for project {project_id}")
        raise AnalysisError(str(e))


@router.post("/{project_id}/analyze-frameworks", status_code=200)
def analyze_project_frameworks(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Analyze frameworks for an existing project.
    This can be called after upload to run detailed detection.
    """
    logger.info(f"Received request to analyze frameworks for project: {project_id}")
    
    service = AnalysisService(db)
    project = service.project_repo.get(project_id)
    
    if not project:
        logger.error(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    try:
        result = service.analyze_frameworks(project_id, project.root_path, project.source_url)
        logger.info(f"Framework analysis completed for project {project_id}")
        return result
    except Exception as e:
        logger.exception(f"Framework analysis failed for project {project_id}")
        raise AnalysisError(str(e))


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
