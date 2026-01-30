"""API endpoint for contributor analysis."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.exceptions import ProjectNotFoundError
from src.models.database import get_db
from src.models.schemas.contributor import (
    ContributorAnalysisDetailResponseSchema,
    ProjectContributorsVisualizationResponse,
)
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
    top_files: int = 10,
    db: Session = Depends(get_db),
) -> ContributorAnalysisDetailResponseSchema:
    """Get detailed analysis for a specific contributor in a project.

    This endpoint provides analysis of a contributor's contributions including:
    - Top contributing areas (backend, frontend, infra, etc.) with share percentages
    - Top N files by lines changed (configurable)

    Args:
        project_id: Project ID
        contributor_id: Contributor ID
        branch: Optional branch to analyze (defaults to current HEAD)
        top_files: Number of top files to return (default: 10)
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
            top_files=top_files,
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


@router.get("/{project_id}/contributors/visualization")
async def get_project_contributors_visualization(
    project_id: int,
    branch: Optional[str] = None,
    top_areas: int = 5,
    top_files: int = 3,
    db: Session = Depends(get_db),
) -> ProjectContributorsVisualizationResponse:
    """Get visualization data for all contributors in a project.

    This endpoint combines contribution metrics with area analysis to provide:
    - Overall contribution percentage for each contributor (relative to project total)
    - Top contributing areas for each contributor  
    - Top files for each contributor

    The response includes:
    - Project-wide statistics (total lines changed, commits, contributors)
    - Contributors sorted by contribution percentage (descending)
    - For each contributor:
      - Contribution percentage (0-100%)
      - Absolute metrics (lines added/deleted, commits, files)
      - Top contributing areas with share percentages
      - Top modified files with lines changed

    Args:
        project_id: Project ID
        branch: Optional branch to analyze (defaults to HEAD)
        top_areas: Number of top areas to return per contributor (default: 5)
        top_files: Number of top files to return per contributor (default: 3)
        db: Database session

    Returns:
        ProjectContributorsVisualizationResponse with visualization data

    Raises:
        HTTPException 404: Project not found
        HTTPException 500: Failed to generate visualization
    """
    # Verify project exists
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # Get visualization data
    service = ContributorAnalysisService(db)
    try:
        result = service.get_project_contributors_visualization(
            project_id=project_id,
            branch=branch or "HEAD",
            top_areas_count=top_areas,
            top_files_count=top_files,
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate contributors visualization",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error generating visualization for project {project_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate contributors visualization",
        )
