"""Snapshots API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.project import (
    SnapshotCurrentMidpointComparisonResponse,
    SnapshotPairResponse,
)
from src.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.post("/{project_id}/create", response_model=SnapshotPairResponse, status_code=201)
async def create_current_and_midpoint_snapshots(
    project_id: int,
    percentage: int = Query(50, ge=1, le=99, description="Start point: percentage through commit history (1–99)"),
    end_percentage: int = Query(100, ge=2, le=100, description="End point: percentage through commit history (2–100, where 100 = current HEAD)"),
    db: Session = Depends(get_db),
):
    """Create snapshots at two user-chosen points in commit history and compare them."""
    service = SnapshotService(db)
    return service.create_current_and_midpoint_snapshots(project_id, percentage=percentage, end_percentage=end_percentage)


@router.delete("/{project_id}/{snapshot_id}", status_code=200)
async def delete_snapshot(
    project_id: int,
    snapshot_id: int,
    db: Session = Depends(get_db),
):
    """Delete a specific snapshot and its associated comparisons."""
    service = SnapshotService(db)
    return service.delete_snapshot(project_id, snapshot_id)


@router.get("/{project_id}/commit-timeline", status_code=200)
async def get_commit_timeline(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Return a lightweight sampled commit list with dates and percentages for the slider."""
    service = SnapshotService(db)
    return service.get_commit_timeline(project_id)


@router.get("/{project_id}/compare", response_model=SnapshotCurrentMidpointComparisonResponse, status_code=200)
async def compare_current_and_midpoint_snapshots(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Compare latest current and midpoint snapshots for a project."""
    service = SnapshotService(db)
    return service.compare_current_and_midpoint(project_id)
