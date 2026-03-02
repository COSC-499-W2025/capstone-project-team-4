"""API endpoints for contributor lookups."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.contributor import ContributorProjectsByUsernameResponseSchema
from src.services.contributor_projects_service import ContributorProjectsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contributors", tags=["contributors"])


@router.get(
    "/github/{github_username}/projects",
    response_model=ContributorProjectsByUsernameResponseSchema,
)
async def get_projects_by_github_username(
    github_username: str,
    db: Session = Depends(get_db),
) -> ContributorProjectsByUsernameResponseSchema:
    """Return projects sorted by lines changed for a GitHub username."""
    service = ContributorProjectsService(db)
    return service.list_projects_by_github_username(github_username)
