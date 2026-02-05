"""Pydantic schemas for snapshot API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SnapshotMetadata(BaseModel):
    """Snapshot metadata for API responses."""

    id: int = Field(..., description="Snapshot ID")
    source_project_id: int = Field(..., description="ID of the source project")
    source_project_name: str = Field(..., description="Name of the source project")
    snapshot_type: str = Field(..., description="Type: 'baseline', 'current', or custom")
    label: str = Field(..., description="User-friendly label (e.g., '2024-02-04 Baseline')")
    snapshot_date: datetime = Field(..., description="When this snapshot was created")
    commit_hash: Optional[str] = Field(None, description="Git commit hash")
    commit_percentage: Optional[float] = Field(None, description="Percentage through git history")
    description: Optional[str] = Field(None, description="Optional description")
    created_at: datetime = Field(..., description="Timestamp when snapshot was created")

    model_config = ConfigDict(from_attributes=True)


class SnapshotResponse(BaseModel):
    """Complete snapshot information including analysis data."""

    # Snapshot metadata
    id: int = Field(..., description="Snapshot ID")
    source_project_id: int = Field(..., description="ID of the source project")
    source_project_name: str = Field(..., description="Name of the source project")
    snapshot_type: str = Field(..., description="Type: 'baseline', 'current', or custom")
    label: str = Field(..., description="User-friendly label")
    snapshot_date: datetime = Field(..., description="When this snapshot was created")
    commit_hash: Optional[str] = Field(None, description="Git commit hash")
    commit_percentage: Optional[float] = Field(None, description="Percentage through git history")
    description: Optional[str] = Field(None, description="Optional description")
    created_at: datetime = Field(..., description="Timestamp when snapshot was created")

    # Analysis data (optional - only if project has been analyzed)
    analyzed_project_id: Optional[int] = Field(None, description="ID of the analyzed project data")
    total_lines: Optional[int] = Field(None, description="Total lines of code")
    num_files: Optional[int] = Field(None, description="Number of files")
    num_contributors: Optional[int] = Field(None, description="Number of contributors")
    complexity_avg: Optional[float] = Field(None, description="Average complexity")

    model_config = ConfigDict(from_attributes=True)


class SnapshotListResponse(BaseModel):
    """Response for listing snapshots."""

    snapshots: list[SnapshotMetadata] = Field(default_factory=list, description="List of snapshots")
    total: int = Field(..., description="Total number of snapshots")
    limit: int = Field(..., description="Number of snapshots requested")
    offset: int = Field(..., description="Number of snapshots skipped")


class SnapshotCreateRequest(BaseModel):
    """Request to create snapshots from uploaded project."""

    project_name: str = Field(..., description="Name of the project")
    baseline_percentage: float = Field(50.0, ge=0.0, le=100.0, description="Percentage for baseline snapshot")
    baseline_label: Optional[str] = Field(None, description="Custom label for baseline snapshot")
    current_label: Optional[str] = Field(None, description="Custom label for current snapshot")
    description: Optional[str] = Field(None, description="Optional description for snapshots")
