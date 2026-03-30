"""Skills API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.skill import (
    ProjectSkillsResponse,
    SkillTimelineResponse,
    SkillSourceResponse,
    SkillsBySourceResponse,
)
from src.services.skill_service import SkillService
from src.services.project_service import ProjectService
from src.api.exceptions import ProjectNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/skills", tags=["skills"])

# Valid source types for skill filtering
VALID_SOURCES = {"language", "framework", "library", "tool", "contextual", "file_type"}


@router.get("", response_model=ProjectSkillsResponse)
async def get_project_skills(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all skills extracted from project analysis.

    - Returns skills grouped by category
    - Includes detected languages and frameworks
    """
    service = SkillService(db)
    result = service.get_project_skills(project_id)

    if not result:
        raise ProjectNotFoundError(project_id)

    return result


@router.get("/categories", response_model=list)
async def get_skill_categories(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all skill categories for a project.

    - Returns list of unique skill categories
    """
    project_service = ProjectService(db)
    if not project_service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    service = SkillService(db)
    return service.get_skill_categories(project_id)


@router.get("/timeline", response_model=SkillTimelineResponse)
async def get_skill_timeline(
    project_id: int,
    skill: Optional[str] = Query(None, description="Filter by specific skill"),
    db: Session = Depends(get_db),
):
    """
    Get skill timeline showing when skills were used.

    - Returns chronological data of skill usage
    - Optionally filter by a specific skill
    """
    service = SkillService(db)
    result = service.get_skill_timeline(project_id, skill)

    if not result:
        raise ProjectNotFoundError(project_id)

    return result

@router.post("/timeline/build", response_model=SkillTimelineResponse)
async def build_skill_timeline(
    project_id: int,
    skill: Optional[str] = Query(None, description="Filter by specific skill"),
    db: Session = Depends(get_db),
):
    logger.info("[TIMELINE ROUTE] project_id=%s", project_id)
    project_service = ProjectService(db)
    if not project_service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    service = SkillService(db)
    result = service.build_skill_timeline(project_id, skill)

    if not result:
        raise ProjectNotFoundError(project_id)

    return result

@router.get("/sources", response_model=SkillSourceResponse)
async def get_skill_sources(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get skills grouped by their detection source.
    """
    project_service = ProjectService(db)
    if not project_service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    service = SkillService(db)
    return service.get_skill_sources(project_id)


@router.get("/by-source/{source}", response_model=SkillsBySourceResponse)
async def get_skills_by_source(
    project_id: int,
    source: str,
    db: Session = Depends(get_db),
):
    """
    Get skills filtered by a specific source type.
    """
    if source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source type. Must be one of: {', '.join(VALID_SOURCES)}"
        )

    project_service = ProjectService(db)
    if not project_service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    service = SkillService(db)
    return service.get_skills_by_source(project_id, source)