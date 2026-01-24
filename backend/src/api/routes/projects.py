"""Projects API routes."""

import logging
from datetime import datetime, date
from typing import Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.project import ProjectList, ProjectDetail
from src.models.schemas.contributor import (
    ProjectContributorsResponse,
    ContributorSchema,
    ProjectContributorsAnalysisResponse,
    ActivitySchema,
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

    # # [LEGACY] Get the ORM model for path attribute (for Git re-analysis)
    # project_repo = ProjectRepository(db)
    # project_orm = project_repo.get(project_id)
    # 
    # if not project_orm:
    #     raise ProjectNotFoundError(project_id)
    # 
    # logger.info(f"Project root_path: {project_orm.root_path}")
    # logger.info(f"Project source_type: {project_orm.source_type}")
    # logger.info(f"Project source_url: {project_orm.source_url}")

    contributor_repo = ContributorRepository(db)
    contributors = contributor_repo.get_by_project(project_id)

    # # [LEGACY] Get activity metrics from Git analysis (re-analyzing on every request)
    # git_contributors = analyze_contributors(project_orm.root_path)
    # 
    # # Debug: log what we're getting
    # if git_contributors:
    #     logger.info(f"First git contributor keys: {git_contributors[0].keys()}")
    #     logger.info(f"Commit dates in first contributor: {git_contributors[0].get('commit_dates', [])[:3]}")
    # 
    # activity_by_email: dict = {}
    # 
    # # Build activity lookup by multiple email variants
    # for git_contrib in git_contributors:
    #     email = git_contrib.get("email", "")
    #     github_email = git_contrib.get("github_email", "")
    #     all_emails = git_contrib.get("all_emails", [])
    #     
    #     commit_dates = git_contrib.get("commit_dates", [])
    #     activity = _calculate_activity_metrics(commit_dates)
    #     
    #     # Store activity by all known email addresses
    #     if email:
    #         activity_by_email[email] = activity
    #     if github_email:
    #         activity_by_email[github_email] = activity
    #     for email_variant in all_emails:
    #         activity_by_email[email_variant] = activity

    contributor_schemas = []
    total_commits = 0

    for c in contributors:
        # Calculate activity metrics from database commit_history
        commit_dates = [commit.commit_date for commit in c.commit_history]
        activity = _calculate_activity_metrics(commit_dates) if commit_dates else ActivitySchema()
        
        # # [LEGACY] Get activity metrics - try multiple email addresses (from Git re-analysis)
        # activity = ActivitySchema()
        # 
        # # Try primary email first
        # if c.email and c.email in activity_by_email:
        #     activity = activity_by_email[c.email]
        # # Try github_email if available
        # elif c.github_email and c.github_email in activity_by_email:
        #     activity = activity_by_email[c.github_email]
        # else:
        #     # Try fuzzy matching: check if any git email contains the DB email username
        #     for git_email, git_activity in activity_by_email.items():
        #         if c.email and "@" in c.email:
        #             db_username = c.email.split("@")[0].lower()
        #             if "@" in git_email and db_username in git_email.lower():
        #                 activity = git_activity
        #                 break
        
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
        ))
        total_commits += c.commits

    return ProjectContributorsResponse(
        project_id=project_id,
        project_name=project_detail.name,
        contributors=contributor_schemas,
        total_contributors=len(contributor_schemas),
        total_commits=total_commits,
    )


@router.get("/{project_id}/contributors/analysis", response_model=ProjectContributorsAnalysisResponse)
async def get_contributor_analysis(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed contribution analysis for each contributor in a project.

    - Returns contribution scores (0-100) for each contributor
    - Scores are calculated using: commits (40%), lines changed (40%), files touched (20%)
    - Also includes absolute metrics: commits, lines added/deleted, files touched
    - Useful for understanding who contributed what to the project
    """
    service = ProjectService(db)
    result = service.get_contributor_analysis(project_id)

    if result is None:
        raise ProjectNotFoundError(project_id)

    return result


# @router.get("/{project_id}/complexity", response_model=ComplexityReport)
# async def get_project_complexity(
#     project_id: int,
#     db: Session = Depends(get_db),
# ):
#     """
#     Get code complexity metrics for a project.

#     - Returns complexity statistics and function-level metrics
#     - Includes high complexity functions for review
#     """
#     service = ProjectService(db)
#     project = service.get_project(project_id)

#     if not project:
#         raise ProjectNotFoundError(project_id)

#     complexity_repo = ComplexityRepository(db)

#     # Get summary
#     summary = complexity_repo.get_summary(project_id)

#     # Get by file
#     grouped = complexity_repo.get_by_file_grouped(project_id)
#     by_file = []

#     for file_path, functions in grouped.items():
#         complexity_values = [f.cyclomatic_complexity for f in functions]
#         function_schemas = [
#             ComplexitySchema(
#                 id=f.id,
#                 file_path=f.file_path,
#                 function_name=f.function_name,
#                 start_line=f.start_line,
#                 end_line=f.end_line,
#                 cyclomatic_complexity=f.cyclomatic_complexity,
#             )
#             for f in functions
#         ]

#         by_file.append(ComplexityByFile(
#             file_path=file_path,
#             function_count=len(functions),
#             avg_complexity=sum(complexity_values) / len(complexity_values) if complexity_values else 0,
#             max_complexity=max(complexity_values) if complexity_values else 0,
#             functions=function_schemas,
#         ))

#     # Get high complexity functions
#     high_complexity = complexity_repo.get_high_complexity(project_id, threshold=10)
#     high_complexity_schemas = [
#         ComplexitySchema(
#             id=f.id,
#             file_path=f.file_path,
#             function_name=f.function_name,
#             start_line=f.start_line,
#             end_line=f.end_line,
#             cyclomatic_complexity=f.cyclomatic_complexity,
#         )
#         for f in high_complexity
#     ]

#     from src.models.schemas.complexity import ComplexitySummary

#     return ComplexityReport(
#         project_id=project_id,
#         project_name=project.name,
#         summary=ComplexitySummary(
#             total_functions=summary.get("total_functions", 0),
#             avg_complexity=summary.get("avg_complexity", 0.0),
#             max_complexity=summary.get("max_complexity", 0),
#             min_complexity=summary.get("min_complexity", 0),
#             high_complexity_count=summary.get("high_complexity_count", 0),
#             medium_complexity_count=summary.get("medium_complexity_count", 0),
#             low_complexity_count=summary.get("low_complexity_count", 0),
#         ),
#         by_file=by_file,
#         high_complexity_functions=high_complexity_schemas,
#     )
