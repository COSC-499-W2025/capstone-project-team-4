"""Pydantic schemas for test data snapshots."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel


class SnapshotArchive(BaseModel):
    """Metadata for a snapshot archive."""

    name: str
    relative_path: str
    size_bytes: int
    modified_at: datetime


class SnapshotArchiveList(BaseModel):
    """List of snapshot archives for a project."""

    project_key: str
    root_dir: str
    items: List[SnapshotArchive] = []


class SnapshotMetrics(BaseModel):
    """Analysis metrics for a single snapshot."""

    snapshot_name: str
    total_commits: int
    contributor_count: int
    languages: List[str]
    frameworks: List[str]
    libraries: List[str]
    tools: List[str]
    skills: List[str]
    skill_count: int
    total_files: int
    total_loc: int
    avg_complexity: Optional[float] = None
    first_commit_date: Optional[str] = None


class MetricComparison(BaseModel):
    """Comparison between two metric values."""

    snapshot1_value: Any
    snapshot2_value: Any
    change: Optional[Any] = None
    percent_change: Optional[float] = None


class SnapshotComparison(BaseModel):
    """Detailed comparison between two snapshots."""

    snapshot1_name: str
    snapshot2_name: str

    # Overall comparison
    summary: str

    # Metric comparisons
    contributors: MetricComparison
    languages: MetricComparison
    frameworks: MetricComparison
    libraries: MetricComparison
    skills: MetricComparison
    total_files: MetricComparison
    total_loc: MetricComparison
    avg_complexity: MetricComparison

    # Detailed metrics
    snapshot1_metrics: SnapshotMetrics
    snapshot2_metrics: SnapshotMetrics

    # What's new in snapshot2
    new_contributors: List[str] = []
    new_languages: List[str] = []
    new_frameworks: List[str] = []
    new_libraries: List[str] = []
    new_skills: List[str] = []
