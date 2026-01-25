"""Projects API routes."""

import logging
from datetime import datetime, date
from typing import Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Body
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.project import ProjectList, ProjectDetail
from src.models.schemas.contributor import (
    ProjectContributorsResponse,
    ContributorSchema,
    ProjectContributorsAnalysisResponse,
    ActivitySchema,
    ChangeStatsSchema,
)
from src.models.schemas.complexity import ComplexityReport, ComplexityByFile, ComplexitySchema
from src.services.project_service import ProjectService
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.complexity_repository import ComplexityRepository
from src.api.exceptions import ProjectNotFoundError
from src.core.analyzers.contributor import analyze_contributors

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

def _find_git_root(start_path: str) -> Optional[str]:
    """Find nearest parent directory containing a .git folder.

    Args:
        start_path: Starting path to search upwards from

    Returns:
        String path of git root or None
    """
    try:
        from pathlib import Path
        p = Path(start_path).resolve()
        # Walk up to 6 levels to be safe
        for _ in range(6):
            if (p / ".git").exists():
                return str(p)
            if p.parent == p:
                break
            p = p.parent
        return None
    except Exception:
        return None


def _calculate_activity_metrics(commit_dates: list) -> ActivitySchema:
    """
    Calculate activity metrics from commit dates.
    
    Args:
        commit_dates: List of datetime objects of commits
        
    Returns:
        ActivitySchema with calculated metrics
    """
    if not commit_dates:
        return ActivitySchema()
    
    # Sort dates
    sorted_dates = sorted(commit_dates)
    
    # Unique dates (active_days)
    unique_dates: Set[date] = set(d.date() if isinstance(d, datetime) else d for d in sorted_dates)
    active_days = len(unique_dates)
    
    # First and last commit dates
    first_commit_date = sorted_dates[0] if sorted_dates else None
    last_commit_date = sorted_dates[-1] if sorted_dates else None
    
    # Active span (days from first to last, inclusive)
    active_span_days = 0
    if first_commit_date and last_commit_date:
        first_date = first_commit_date.date() if isinstance(first_commit_date, datetime) else first_commit_date
        last_date = last_commit_date.date() if isinstance(last_commit_date, datetime) else last_commit_date
        active_span_days = (last_date - first_date).days + 1
    
    # Active day ratio
    active_day_ratio = 0.0
    if active_span_days > 0:
        active_day_ratio = round(active_days / active_span_days, 2)
    
    # Unique weeks (ISO week)
    unique_weeks: Set[tuple] = set()
    for d in sorted_dates:
        date_obj = d.date() if isinstance(d, datetime) else d
        iso_year, iso_week, _ = date_obj.isocalendar()
        unique_weeks.add((iso_year, iso_week))
    active_weeks = len(unique_weeks)
    
    return ActivitySchema(
        active_days=active_days,
        first_commit_date=first_commit_date,
        last_commit_date=last_commit_date,
        active_span_days=active_span_days,
        active_day_ratio=active_day_ratio,
        active_weeks=active_weeks,
    )


# fixing this function
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


# @router.get("/{project_id}", response_model=ProjectDetail)
# async def get_project(
#     project_id: int,
#     db: Session = Depends(get_db),
# ):
#     """
#     Get detailed information about a specific project.

#     - Returns full project details including languages, frameworks, and metrics
#     """
#     service = ProjectService(db)
#     project = service.get_project(project_id)

#     if not project:
#         raise ProjectNotFoundError(project_id)

#     return project


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
    project_detail = service.get_project(project_id)

    if not project_detail:
        raise ProjectNotFoundError(project_id)

    contributor_repo = ContributorRepository(db)
    contributors = contributor_repo.get_by_project(project_id)



    contributor_schemas = []
    total_commits = 0

    for c in contributors:
        # Calculate activity metrics from database commit_history
        commit_dates = [commit.commit_date for commit in c.commit_history]
        activity = _calculate_activity_metrics(commit_dates) if commit_dates else ActivitySchema()
        
        # Filter out .json files from files_modified
        all_files = c.files_modified or []
        non_json_files = [fm for fm in all_files if not (fm.filename or "").lower().endswith(".json")]
        json_count = len(all_files) - len(non_json_files)
        
        logger.debug(f"Contributor {c.name}: total={len(all_files)} files, json={json_count}, non_json={len(non_json_files)}")
        if json_count > 0:
            logger.debug(f"  JSON files: {[fm.filename for fm in all_files if (fm.filename or '').lower().endswith('.json')]}")
        
        # Calculate change statistics (excluding .json files)
        total_lines_changed = c.total_lines_added + c.total_lines_deleted
        lines_changed_per_commit = round(total_lines_changed / c.commits, 2) if c.commits > 0 else 0.0
        files_changed = len(non_json_files)
        
        changes = ChangeStatsSchema(
            total_lines_added=c.total_lines_added,
            total_lines_deleted=c.total_lines_deleted,
            total_lines_changed=total_lines_changed,
            lines_changed_per_commit=lines_changed_per_commit,
            files_changed=files_changed,
        )
        
        contributor_schemas.append(ContributorSchema(
            id=c.id,
            name=c.name,
            email=c.email,
            github_username=c.github_username,
            github_email=c.github_email,
            commits=c.commits,
            commit_percent=c.percent,
            total_lines_added=c.total_lines_added,
            total_lines_deleted=c.total_lines_deleted,
            activity=activity,
            changes=changes,
        ))
        total_commits += c.commits

    return ProjectContributorsResponse(
        project_id=project_id,
        project_name=project_detail.name,
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
        project_name=project.name,
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
