"""Snapshots API routes."""

from fastapi import APIRouter, Depends
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
    db: Session = Depends(get_db),
):
    """Create current and midpoint snapshots in one call."""
    service = SnapshotService(db)
    return service.create_current_and_midpoint_snapshots(project_id)


@router.get("/{project_id}/compare", response_model=SnapshotCurrentMidpointComparisonResponse, status_code=200)
async def compare_current_and_midpoint_snapshots(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Compare latest current and midpoint snapshots for a project."""
    service = SnapshotService(db)
    return service.compare_current_and_midpoint(project_id)
