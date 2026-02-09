"""API endpoint for contributor analysis."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.exceptions import ProjectNotFoundError
from src.models.database import get_db
from src.models.schemas.contributor import ContributorAnalysisDetailResponseSchema
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.project_repository import ProjectRepository
from src.services.contributor_analysis_service import ContributorAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["contributors"])


@router.get("/{project_id}/contributors/{contributor_id}/analysis")
async def get_contributor_analysis(
    project_id: int,
    contributor_id: int,
    branch: Optional[str] = None,
    db: Session = Depends(get_db),
) -> ContributorAnalysisDetailResponseSchema:
    """Get detailed analysis for a specific contributor in a project.

    This endpoint provides analysis of a contributor's contributions including:
    - Top contributing areas (backend, frontend, infra, etc.) with share percentages
    - Top 10 files by lines changed

    Args:
        project_id: Project ID
        contributor_id: Contributor ID
        branch: Optional branch to analyze (defaults to current HEAD)
        db: Database session

    Returns:
        ContributorAnalysisDetailResponseSchema with contributor analysis

    Raises:
        HTTPException 404: Project or Contributor not found
        HTTPException 400: Contributor does not belong to project or branch not found
    """
    # Verify project exists
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # Verify contributor exists
    contributor_repo = ContributorRepository(db)
    contributor = contributor_repo.get(contributor_id)
    if not contributor:
        raise HTTPException(
            status_code=404, detail=f"Contributor {contributor_id} not found"
        )

    # Verify contributor belongs to project
    if contributor.project_id != project_id:
        raise HTTPException(
            status_code=400,
            detail=f"Contributor {contributor_id} does not belong to project {project_id}",
        )

    # Get analysis
    service = ContributorAnalysisService(db)
    try:
        analysis = service.get_contributor_analysis(
            project_id=project_id,
            contributor_id=contributor_id,
            branch=branch,
        )

        if not analysis:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate contributor analysis",
            )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing contributor {contributor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze contributor contributions",
        )
