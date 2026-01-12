"""Skills API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.skill import ProjectSkillsResponse, SkillTimelineResponse
from src.services.skill_service import SkillService
from src.services.project_service import ProjectService
from src.api.exceptions import ProjectNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/skills", tags=["skills"])


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


@router.get("/categories", response_model=list)
async def get_skill_categories(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all skill categories for a project.

    - Returns list of unique skill categories
    """
    # First check if project exists
    project_service = ProjectService(db)
    if not project_service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    service = SkillService(db)
    return service.get_skill_categories(project_id)
