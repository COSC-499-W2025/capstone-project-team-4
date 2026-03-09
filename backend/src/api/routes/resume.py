"""Resume API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.resume import (
    ProjectResumeResponse,
    ResumeItemSchema,
    ResumeItemUpdate,
)
from src.services.resume_service import ResumeService
from src.services.project_service import ProjectService
from src.api.exceptions import ProjectNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/resume", tags=["resume"])


@router.get("", response_model=ProjectResumeResponse)
async def get_project_resume(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all resume items for a project.

    - Returns generated resume bullet points
    - May include multiple versions if regenerated
    """
    service = ResumeService(db)
    result = service.get_project_resume(project_id)

    if not result:
        raise ProjectNotFoundError(project_id)

    return result


@router.get("/latest", response_model=ResumeItemSchema)
async def get_latest_resume_item(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the most recent resume item for a project.

    - Returns the latest generated resume with title and highlights
    """
    # First check if project exists
    project_service = ProjectService(db)
    if not project_service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    service = ResumeService(db)
    result = service.get_latest_resume_item(project_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No resume items found for project {project_id}",
        )

    return result


@router.post("/regenerate", response_model=ResumeItemSchema, status_code=201)
async def regenerate_resume(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Regenerate resume item based on current analysis data.

    - Creates a new resume item with updated bullet points
    - Previous resume items are preserved
    """
    service = ResumeService(db)
    result = service.regenerate_resume(project_id)

    if not result:
        raise ProjectNotFoundError(project_id)

    return result


@router.patch("/{resume_id}", response_model=ResumeItemSchema)
async def update_resume_item(
    project_id: int,
    resume_id: int,
    update: ResumeItemUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing resume item.

    - Allows editing title and highlights
    - Only updates provided fields
    """
    # First check if project exists
    project_service = ProjectService(db)
    if not project_service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    service = ResumeService(db)
    result = service.update_resume_item(
        resume_id=resume_id,
        title=update.title,
        highlights=update.highlights,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Resume item {resume_id} not found",
        )

    return result
