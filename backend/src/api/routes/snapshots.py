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
