"""Analysis API routes."""

import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional

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


@router.post("/upload", response_model=AnalysisResult, status_code=201)
async def analyze_upload(
    file: UploadFile = File(..., description="ZIP file to analyze"),
    project_name: Optional[str] = Form(None, description="Custom project name"),
    db: Session = Depends(get_db),
):
    """
    Analyze a project from an uploaded ZIP file.

    - Upload a ZIP file containing the project source code
    - Optionally specify a custom project name
    - Returns analysis results including languages, frameworks, skills, and complexity metrics
    """
    # Validate file type
    if not file.filename:
        raise InvalidFileError("No filename provided")

    if not file.filename.lower().endswith(".zip"):
        raise InvalidFileError("File must be a ZIP archive")

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        try:
            # Read and write in chunks to handle large files
            contents = await file.read()
            tmp.write(contents)
            tmp_path = Path(tmp.name)
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise InvalidFileError(f"Failed to save file: {str(e)}")

    try:
        # Run analysis
        service = AnalysisService(db)
        name = project_name or Path(file.filename).stem
        result = service.analyze_from_zip(tmp_path, name)
        return result

    except FileNotFoundError as e:
        raise InvalidFileError(str(e))
    except ValueError as e:
        raise InvalidFileError(str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise AnalysisError(str(e))
    finally:
        # Clean up temp file
        try:
            tmp_path.unlink()
        except Exception:
            pass


# @router.post("/github", response_model=AnalysisResult, status_code=201)
# async def analyze_github(
#     request: GitHubAnalysisRequest,
#     db: Session = Depends(get_db),
# ):
#     """
#     Analyze a project from a GitHub repository URL.

#     - Provide a GitHub repository URL (public repos only)
#     - Optionally specify a branch to analyze
#     - The repository will be cloned and analyzed
#     - Returns analysis results including languages, frameworks, skills, and complexity metrics
#     """
#     github_url = str(request.github_url)

#     # Validate GitHub URL
#     if "github.com" not in github_url:
#         raise InvalidGitHubURLError(github_url)

#     try:
#         service = AnalysisService(db)
#         result = service.analyze_from_github(
#             github_url=github_url,
#             branch=request.branch,
#         )
#         return result

#     except ValueError as e:
#         raise InvalidGitHubURLError(str(e))
#     except RuntimeError as e:
#         raise AnalysisError(str(e))
#     except Exception as e:
#         logger.error(f"GitHub analysis failed: {e}")
#         raise AnalysisError(str(e))


# @router.post("/directory", response_model=AnalysisResult, status_code=201)
# async def analyze_directory(
#     directory_path: str = Form(..., description="Path to local directory"),
#     project_name: Optional[str] = Form(None, description="Custom project name"),
#     db: Session = Depends(get_db),
# ):
#     """
#     Analyze a project from a local directory.

#     - Provide the absolute path to a local project directory
#     - Optionally specify a custom project name
#     - Returns analysis results including languages, frameworks, skills, and complexity metrics

#     Note: This endpoint is intended for local/development use.
#     """
#     path = Path(directory_path)

#     if not path.exists():
#         raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")

#     if not path.is_dir():
#         raise HTTPException(status_code=400, detail=f"Path is not a directory: {directory_path}")

#     try:
#         service = AnalysisService(db)
#         name = project_name or path.name
#         result = service.analyze_from_directory(path, name)
#         return result

#     except Exception as e:
#         logger.error(f"Directory analysis failed: {e}")
#         raise AnalysisError(str(e))
