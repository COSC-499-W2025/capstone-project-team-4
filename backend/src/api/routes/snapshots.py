"""Snapshots API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.project import ProjectSnapshotResponse
from src.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.post("/{project_id}/midpoint", response_model=ProjectSnapshotResponse, status_code=201)
async def create_midpoint_snapshot(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Create midpoint snapshot for a project and save it in DB."""
    service = SnapshotService(db)
    return service.create_midpoint_snapshot(project_id)

