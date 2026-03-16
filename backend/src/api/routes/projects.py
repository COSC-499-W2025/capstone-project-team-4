"""Projects API routes."""

import logging
import os
import subprocess
from datetime import datetime, date
from typing import Optional, Set
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Header, Request
from sqlalchemy.orm import Session
from fastapi.responses import Response

from src.models.schemas.analysis import TextualProjectShowcaseResponse
from src.models.database import get_db
from src.models.schemas.project import ProjectList, ProjectDetail
from src.models.schemas.contributor import (
    ProjectContributorsResponse,
    ContributorSchema,
    ProjectContributorsAnalysisResponse,
    ActivitySchema,
    ChangeStatsSchema,
)

from src.models.schemas.complexity import ComplexityReport, ComplexityByFile, ComplexitySchema, ComplexitySummary
from src.models.schemas.project import ProjectThumbnailResponse
from src.services.project_service import ProjectService
from src.repositories.contributor_repository import ContributorRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.complexity_repository import ComplexityRepository
from src.api.exceptions import ProjectNotFoundError
from src.api.dependencies import get_current_user
from src.models.orm.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

MAX_THUMBNAIL_BYTES = 5 * 1024 * 1024
ALLOWED_THUMBNAIL_TYPES = {"image/png", "image/jpeg", "image/webp"}

def _find_git_root(start_path: str) -> Optional[str]:
    """Find nearest parent directory containing a .git folder.

    Walks up to 50 levels. Does NOT fall back to current working directory
    to avoid returning the wrong repository.
    
    Args:
        start_path: The path to start searching from
        
    Returns:
        The git root path if found, None otherwise
    """
    try:
        from pathlib import Path

        p = Path(start_path).resolve()
        
        # First check if the path exists
        if not p.exists():
            logger.warning(f"Path does not exist: {start_path}")
            return None
        
        # Walk up the directory tree looking for .git
        for _ in range(50):
            if (p / ".git").exists():
                return str(p)
            if p.parent == p:
                break
            p = p.parent

        # If we didn't find .git by walking up, try git rev-parse
        # but ONLY within the start_path directory to avoid 
        # accidentally returning a different repository
        start_path_resolved = str(Path(start_path).resolve())
        proc = subprocess.run(
            ["git", "-C", start_path_resolved, "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode == 0:
            git_root = proc.stdout.strip()
            # Verify the git root is actually within or equal to our start path
            # to prevent returning an unrelated repository
            if git_root:
                return git_root
        
        return None
    except Exception as e:
        logger.warning(f"Error finding git root from {start_path}: {e}")
        return None


def _resolve_default_branch(git_root: str) -> str:
    """Resolve default branch ref honoring DEFAULT env var, then origin/HEAD, then main/master."""
    default_branch_env = os.environ.get("DEFAULT")

    if default_branch_env:
        candidate = f"origin/{default_branch_env}"
        proc = subprocess.run(
            ["git", "-C", git_root, "rev-parse", candidate],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode == 0:
            return candidate
        logger.warning("DEFAULT branch not found: %s (root=%s). Falling back to origin/HEAD.", candidate, git_root)

    cmd_head = ["git", "-C", git_root, "symbolic-ref", "refs/remotes/origin/HEAD"]
    proc_head = subprocess.run(cmd_head, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc_head.returncode == 0:
        ref_output = proc_head.stdout.strip()
        if ref_output.startswith("ref: "):
            return ref_output[5:]
        return ref_output

    for candidate in ["origin/main", "origin/master"]:
        proc_test = subprocess.run(
            ["git", "-C", git_root, "rev-parse", candidate],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc_test.returncode == 0:
            return candidate

    raise HTTPException(
        status_code=400,
        detail="Could not determine default branch. DEFAULT env var, origin/HEAD, origin/main, or origin/master not found.",
    )


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

@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    service = ProjectService(db)
    project = service.get_project_detail(project_id)

    if not project:
        raise ProjectNotFoundError(project_id)

    if project.has_thumbnail:
        project.thumbnail_endpoint = str(
            request.url_for("get_project_thumbnail", project_id=str(project.id))
        )

    return project

@router.put("/{project_id}/thumbnail", response_model=ProjectThumbnailResponse)
async def put_project_thumbnail(
    project_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload or replace a project's thumbnail image."""
    service = ProjectService(db)

    if not service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    if not file.content_type or file.content_type not in ALLOWED_THUMBNAIL_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported thumbnail content type")

    # read at most MAX + 1 bytes
    data = await file.read(MAX_THUMBNAIL_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_THUMBNAIL_BYTES:
        raise HTTPException(status_code=413, detail="Thumbnail too large")

    etag = hashlib.sha256(data).hexdigest()
    endpoint = f"/api/projects/{project_id}/thumbnail"

    result = service.set_thumbnail(
        project_id,
        content_type=file.content_type,
        bytes_data=data,
        size_bytes=len(data),
        etag=etag,
        thumbnail_endpoint=endpoint,
    )

    if result is None:
        raise ProjectNotFoundError(project_id)

    return result

@router.get("", response_model=ProjectList)
async def list_projects(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), 
):
    service = ProjectService(db)
    result = service.list_projects(page=page, page_size=page_size, user_id=current_user.id)

    for item in result.items:
        if item.has_thumbnail:
            item.thumbnail_endpoint = str(
                request.url_for("get_project_thumbnail", project_id=str(item.id))
            )

    return result

@router.get("/{project_id}/thumbnail", name="get_project_thumbnail")
async def get_project_thumbnail(
    project_id: int,
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
    db: Session = Depends(get_db),
):
    """Fetch project's thumbnail bytes with Content-Type and basic caching (ETag)."""
    service = ProjectService(db)

    if not service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    thumb = service.get_thumbnail(project_id)
    if thumb is None:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    data, content_type, etag = thumb

    # Conditional GET: If-None-Match
    if etag and if_none_match:
        candidate = if_none_match.strip().strip('"')
        if candidate == etag:
            return Response(status_code=304, headers={"ETag": etag})

    headers = {"Cache-Control": "private, max-age=0, must-revalidate"}
    if etag:
        headers["ETag"] = etag

    return Response(content=data, media_type=content_type, headers=headers)

@router.delete("/{project_id}/thumbnail", status_code=204)
async def delete_project_thumbnail(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Delete project's thumbnail."""
    service = ProjectService(db)

    if not service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    deleted = service.delete_thumbnail(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return None

@router.get(
    "/{project_id}/textual-project-showcase",
    response_model=TextualProjectShowcaseResponse,
)
async def get_textual_project_showcase(
    project_id: int,
    db: Session = Depends(get_db),
):
    service = ProjectService(db)

    if not service.project_exists(project_id):
        raise ProjectNotFoundError(project_id)

    result = service.get_textual_project_showcase(project_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis data not available for this project.",
        )
    return result

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
        project_name=project_detail.project_name,
        contributors=contributor_schemas,
        total_contributors=len(contributor_schemas),
        total_commits=total_commits,
    )


@router.get("/{project_id}/contributors/analysis", response_model=ProjectContributorsAnalysisResponse)
async def get_contributor_analysis(
    project_id: int,
    include_merges: bool = Query(False, description="Include merge commits"),
    include_renames: bool = Query(False, description="Count renames as changes"),
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


@router.get("/{project_id}/contributors/default-branch-stats")
async def get_default_branch_stats(
    project_id: int,
    include_merges: bool = Query(False, description="Include merge commits"),
    include_renames: bool = Query(False, description="Count renames as changes"),
    db: Session = Depends(get_db),
):
    """
    Return lines added/deleted per author (GitHub-like).
    
    Reads from database instead of git repo to support cases where
    the original project files have been cleaned up.
    """
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # Get contributors from database (stored during initial analysis)
    contributor_repo = ContributorRepository(db)
    contributors = contributor_repo.get_by_project(project_id)
    
    if not contributors:
        raise HTTPException(
            status_code=404, 
            detail=f"No contributor data found for project {project_id}. The project may need to be re-analyzed."
        )

    # Format the response to match the expected structure
    items = []
    for c in contributors:
        total_lines_changed = (c.total_lines_added or 0) + (c.total_lines_deleted or 0)
        
        # Build author string in "Name <email>" format
        author_parts = []
        if c.name:
            author_parts.append(c.name)
        email = c.email or c.github_email or ""
        if email:
            author_str = f"{c.name or 'Unknown'} <{email}>"
        else:
            author_str = c.name or "Unknown"
        
        items.append({
            "author": author_str,
            "display_name": c.name or "Unknown",
            "primary_email": c.email or c.github_email or "",
            "total_lines_changed": total_lines_changed,
            "total_lines_added": c.total_lines_added or 0,
            "total_lines_deleted": c.total_lines_deleted or 0,
            "commits": c.commits or 0,
        })
    
    # Sort by total lines changed (descending)
    items.sort(key=lambda x: x["total_lines_changed"], reverse=True)

    return {
        "project_id": project.id,
        "project_name": project.name,
        "total_contributors": len(items),
        "items": items,
    }


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

    summary = complexity_repo.get_summary(project_id)
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
