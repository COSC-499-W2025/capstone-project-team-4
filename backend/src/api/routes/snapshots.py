"""Snapshots API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.api.exceptions import ProjectNotFoundError
from src.models.database import get_db
from src.models.orm.user import User
from src.models.schemas.project import (
    SnapshotCurrentMidpointComparisonResponse,
    SnapshotPairResponse,
)
from src.services.project_service import ProjectService
from src.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


def _require_project_owner(project_service: ProjectService, project_id: int, current_user: User) -> None:
    if not project_service.user_owns_project(project_id, current_user.id):
        raise ProjectNotFoundError(project_id)


@router.post("/{project_id}/create", response_model=SnapshotPairResponse, status_code=201)
async def create_current_and_midpoint_snapshots(
    project_id: int,
    percentage: int = Query(50, ge=1, le=99, description="Start point: percentage through commit history (1–99)"),
    end_percentage: int = Query(100, ge=2, le=100, description="End point: percentage through commit history (2–100, where 100 = current HEAD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create snapshots at two user-chosen points in commit history and compare them."""
    _require_project_owner(ProjectService(db), project_id, current_user)
    service = SnapshotService(db)
    return service.create_current_and_midpoint_snapshots(project_id, percentage=percentage, end_percentage=end_percentage)


@router.delete("/{project_id}/{snapshot_id}", status_code=200)
async def delete_snapshot(
    project_id: int,
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific snapshot and its associated comparisons."""
    _require_project_owner(ProjectService(db), project_id, current_user)
    service = SnapshotService(db)
    return service.delete_snapshot(project_id, snapshot_id)


@router.get("/{project_id}/commit-timeline", status_code=200)
async def get_commit_timeline(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a lightweight sampled commit list with dates and percentages for the slider."""
    _require_project_owner(ProjectService(db), project_id, current_user)
    service = SnapshotService(db)
    return service.get_commit_timeline(project_id)


@router.get("/{project_id}/compare", response_model=SnapshotCurrentMidpointComparisonResponse, status_code=200)
async def compare_current_and_midpoint_snapshots(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare latest current and midpoint snapshots for a project."""
    _require_project_owner(ProjectService(db), project_id, current_user)
    service = SnapshotService(db)
    return service.compare_current_and_midpoint(project_id)

@router.get("/{project_id}/activity-heatmap", status_code=200)
async def get_snapshot_activity_heatmap(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return snapshot activity counts grouped by day for heatmap display."""
    _require_project_owner(ProjectService(db), project_id, current_user)
    service = SnapshotService(db)
    return service.get_snapshot_activity_heatmap(project_id)