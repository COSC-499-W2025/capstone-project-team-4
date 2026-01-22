"""Projects API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.project import ProjectList
from src.models.schemas.analysis import AnalysisResult
from src.models.schemas.contributor import ProjectContributorsResponse, ContributorSchema
from src.models.schemas.complexity import ComplexityReport, ComplexityByFile, ComplexitySchema
from src.services.project_service import ProjectService
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.complexity_repository import ComplexityRepository
from src.api.exceptions import ProjectNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectList)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List all analyzed projects with pagination.

    - Returns a paginated list of project summaries
    - Includes basic stats like file count, language count, skill count
    """
    service = ProjectService(db)
    return service.list_projects(page=page, page_size=page_size)


@router.get("/{project_id}", response_model=AnalysisResult)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific project.

    - Returns full project details including languages, frameworks, and metrics
    """
    service = ProjectService(db)
    project = service.get_project(project_id)

    if not project:
        raise ProjectNotFoundError(project_id)

    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a project and all associated data.

    - Permanently deletes the project and all related analysis data
    - This action cannot be undone
    """
    service = ProjectService(db)
    deleted = service.delete_project(project_id)

    if not deleted:
        raise ProjectNotFoundError(project_id)


@router.get("/{project_id}/contributors", response_model=ProjectContributorsResponse)
async def get_project_contributors(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get contributors for a project from git history analysis.

    - Returns list of contributors with their commit stats
    - Includes lines added/deleted and contribution percentage
    """
    service = ProjectService(db)
    project = service.get_project(project_id)

    if not project:
        raise ProjectNotFoundError(project_id)

    contributor_repo = ContributorRepository(db)
    contributors = contributor_repo.get_by_project(project_id)

    contributor_schemas = []
    total_commits = 0

    for c in contributors:
        contributor_schemas.append(ContributorSchema(
            id=c.id,
            name=c.name,
            email=c.email,
            github_username=c.github_username,
            github_email=c.github_email,
            commits=c.commits,
            percent=c.percent,
            total_lines_added=c.total_lines_added,
            total_lines_deleted=c.total_lines_deleted,
        ))
        total_commits += c.commits

    return ProjectContributorsResponse(
        project_id=project_id,
        project_name=project.project_name,
        contributors=contributor_schemas,
        total_contributors=len(contributor_schemas),
        total_commits=total_commits,
    )


@router.get("/{project_id}/complexity", response_model=ComplexityReport)
async def get_project_complexity(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get code complexity metrics for a project.

    - Returns complexity statistics and function-level metrics
    - Includes high complexity functions for review
    """
    service = ProjectService(db)
    project = service.get_project(project_id)

    if not project:
        raise ProjectNotFoundError(project_id)

    complexity_repo = ComplexityRepository(db)

    # Get summary
    summary = complexity_repo.get_summary(project_id)

    # Get by file
    grouped = complexity_repo.get_by_file_grouped(project_id)
    by_file = []

    for file_path, functions in grouped.items():
        complexity_values = [f.cyclomatic_complexity for f in functions]
        function_schemas = [
            ComplexitySchema(
                id=f.id,
                file_path=f.file_path,
                function_name=f.function_name,
                start_line=f.start_line,
                end_line=f.end_line,
                cyclomatic_complexity=f.cyclomatic_complexity,
            )
            for f in functions
        ]

        by_file.append(ComplexityByFile(
            file_path=file_path,
            function_count=len(functions),
            avg_complexity=sum(complexity_values) / len(complexity_values) if complexity_values else 0,
            max_complexity=max(complexity_values) if complexity_values else 0,
            functions=function_schemas,
        ))

    # Get high complexity functions
    high_complexity = complexity_repo.get_high_complexity(project_id, threshold=10)
    high_complexity_schemas = [
        ComplexitySchema(
            id=f.id,
            file_path=f.file_path,
            function_name=f.function_name,
            start_line=f.start_line,
            end_line=f.end_line,
            cyclomatic_complexity=f.cyclomatic_complexity,
        )
        for f in high_complexity
    ]

    from src.models.schemas.complexity import ComplexitySummary

    return ComplexityReport(
        project_id=project_id,
        project_name=project.project_name,
        summary=ComplexitySummary(
            total_functions=summary.get("total_functions", 0),
            avg_complexity=summary.get("avg_complexity", 0.0),
            max_complexity=summary.get("max_complexity", 0),
            min_complexity=summary.get("min_complexity", 0),
            high_complexity_count=summary.get("high_complexity_count", 0),
            medium_complexity_count=summary.get("medium_complexity_count", 0),
            low_complexity_count=summary.get("low_complexity_count", 0),
        ),
        by_file=by_file,
        high_complexity_functions=high_complexity_schemas,
    )
