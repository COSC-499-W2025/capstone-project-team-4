"""Snapshot routes for project progression analysis."""

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.database import get_db
from src.models.schemas.test_data import (
    SnapshotArchive,
    SnapshotArchiveList,
    SnapshotComparison,
)
from src.models.schemas.snapshot import (
    SnapshotMetadata,
    SnapshotResponse,
    SnapshotListResponse,
)
from src.repositories.snapshot_repository import SnapshotRepository

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("/archives", response_model=SnapshotArchiveList)
async def list_snapshot_archives():
    """List available snapshot archives."""
    root_dir = settings.base_dir / "test-data" / "code-collab-proj-snapshots"
    if not root_dir.exists():
        raise HTTPException(status_code=404, detail="Snapshot directory not found.")

    items: list[SnapshotArchive] = []
    for zip_path in sorted(root_dir.glob("*.zip")):
        stat = zip_path.stat()
        items.append(
            SnapshotArchive(
                name=zip_path.name,
                relative_path=str(zip_path.relative_to(settings.base_dir)),
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            )
        )

    return SnapshotArchiveList(
        project_key="code-collab-proj",
        root_dir=str(root_dir.relative_to(settings.base_dir)),
        items=items,
    )


@router.get("/compare", response_model=SnapshotComparison)
async def compare_snapshots(
    project1_id: int = Query(..., description="ID of first project"),
    project2_id: int = Query(..., description="ID of second project"),
    db: Session = Depends(get_db),
):
    """
    Compare two analyzed projects and return the differences.

    Retrieves comparison from database if it exists, otherwise creates it.

    Query parameters:
    - project1_id: ID of first project
    - project2_id: ID of second project

    Example: ?project1_id=1&project2_id=2

    Returns:
    - Metrics for each project
    - Comparison of key metrics
    - What's new in the second project
    """
    from src.services.snapshot_service import SnapshotService

    snapshot_service = SnapshotService(db)

    # Get or create comparison (uses database if exists)
    try:
        comparison = snapshot_service.get_comparison_schema(project1_id, project2_id)
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Snapshot Record Management Endpoints


@router.get("/records", response_model=SnapshotListResponse)
async def list_snapshot_records(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of snapshots to return"),
    offset: int = Query(0, ge=0, description="Number of snapshots to skip"),
    db: Session = Depends(get_db)
):
    """
    List all snapshot records with pagination.

    Returns snapshot metadata including source project info, snapshot type, labels,
    commit information, and creation timestamps.

    Query parameters:
    - limit: Maximum number of snapshots to return (1-1000, default 100)
    - offset: Number of snapshots to skip (default 0)

    Returns:
    - List of snapshot metadata
    - Total count of snapshots
    - Pagination info (limit, offset)
    """
    snapshot_repo = SnapshotRepository(db)

    snapshots = snapshot_repo.list_all(limit=limit, offset=offset)
    total = snapshot_repo.count()

    snapshot_data = [
        SnapshotMetadata(
            id=s.id,
            source_project_id=s.source_project_id,
            source_project_name=s.source_project.name,
            snapshot_type=s.snapshot_type,
            label=s.label,
            snapshot_date=s.snapshot_date,
            commit_hash=s.commit_hash,
            commit_percentage=s.commit_percentage,
            description=s.description,
            created_at=s.created_at,
        )
        for s in snapshots
    ]

    return SnapshotListResponse(
        snapshots=snapshot_data,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/records/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot_record(
    snapshot_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific snapshot record.

    Returns snapshot metadata along with analysis summary metrics if the
    snapshot has been analyzed.

    Path parameters:
    - snapshot_id: ID of the snapshot record

    Returns:
    - Snapshot metadata (label, type, commit info, dates)
    - Analysis summary (LOC, file count, contributors, complexity)

    Raises:
    - 404: If snapshot not found
    """
    snapshot_repo = SnapshotRepository(db)

    snapshot = snapshot_repo.get(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    analyzed_project = snapshot.analyzed_project

    # Build response with metadata and optional analysis data
    response_data = {
        "id": snapshot.id,
        "source_project_id": snapshot.source_project_id,
        "source_project_name": snapshot.source_project.name,
        "snapshot_type": snapshot.snapshot_type,
        "label": snapshot.label,
        "snapshot_date": snapshot.snapshot_date,
        "commit_hash": snapshot.commit_hash,
        "commit_percentage": snapshot.commit_percentage,
        "description": snapshot.description,
        "created_at": snapshot.created_at,
    }

    # Add analysis summary if project exists
    if analyzed_project:
        response_data["analyzed_project_id"] = analyzed_project.id
        response_data["total_lines"] = analyzed_project.total_lines
        response_data["num_files"] = analyzed_project.num_files
        response_data["num_contributors"] = analyzed_project.num_contributors
        response_data["complexity_avg"] = analyzed_project.complexity_avg

    return SnapshotResponse(**response_data)


@router.get("/projects/{project_id}/records", response_model=List[SnapshotMetadata])
async def get_project_snapshot_records(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all snapshot records for a specific source project.

    Returns snapshots in reverse chronological order (newest first).

    Path parameters:
    - project_id: ID of the source project

    Returns:
    - List of snapshot metadata for this project
    """
    snapshot_repo = SnapshotRepository(db)

    snapshots = snapshot_repo.get_by_source_project(project_id)

    return [
        SnapshotMetadata(
            id=s.id,
            source_project_id=s.source_project_id,
            source_project_name=s.source_project.name,
            snapshot_type=s.snapshot_type,
            label=s.label,
            snapshot_date=s.snapshot_date,
            commit_hash=s.commit_hash,
            commit_percentage=s.commit_percentage,
            description=s.description,
            created_at=s.created_at,
        )
        for s in snapshots
    ]


@router.delete("/records/{snapshot_id}")
async def delete_snapshot_record(
    snapshot_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a snapshot record and its analyzed project data (cascade).

    This permanently removes:
    - The snapshot metadata record
    - The associated analyzed project
    - All related comparisons involving this snapshot

    Path parameters:
    - snapshot_id: ID of the snapshot to delete

    Returns:
    - Success message

    Raises:
    - 404: If snapshot not found
    """
    snapshot_repo = SnapshotRepository(db)

    success = snapshot_repo.delete(snapshot_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    return {"message": f"Snapshot {snapshot_id} deleted successfully"}
