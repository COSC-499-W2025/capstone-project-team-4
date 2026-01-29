"""Pydantic schemas for contributors."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActivitySchema(BaseModel):
    """Schema for contributor activity metrics."""

    model_config = ConfigDict(from_attributes=True)

    active_days: int = 0  # Unique dates with commits
    first_commit_date: Optional[datetime] = None  # Earliest commit (ISO 8601)
    last_commit_date: Optional[datetime] = None  # Latest commit (ISO 8601)
    active_span_days: int = 0  # Days from first to last commit (inclusive)
    active_day_ratio: float = 0.0  # active_days / active_span_days
    active_weeks: int = 0  # Unique ISO weeks with commits


class ChangeStatsSchema(BaseModel):
    """Schema for contributor change statistics."""

    model_config = ConfigDict(from_attributes=True)

    total_lines_added: int = 0  # Total lines added across all commits
    total_lines_deleted: int = 0  # Total lines deleted across all commits
    total_lines_changed: int = 0  # added + deleted
    lines_changed_per_commit: float = 0.0  # total_lines_changed / commits
    files_changed: int = 0  # Number of unique files touched


class ContributorFileSchema(BaseModel):
    """Schema for contributor file modifications."""

    model_config = ConfigDict(from_attributes=True)

    filename: str
    modifications: int


class ContributorSchema(BaseModel):
    """Schema for contributor summary."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    github_username: Optional[str] = None
    github_email: Optional[str] = None
    commits: int = 0
    commit_percent: float = Field(0.0, alias="percent", serialization_alias="commit_percent")
    total_lines_added: int = 0
    total_lines_deleted: int = 0
    activity: ActivitySchema = Field(default_factory=ActivitySchema)
    changes: ChangeStatsSchema = Field(default_factory=ChangeStatsSchema)


class ContributorDetailSchema(ContributorSchema):
    """Schema for detailed contributor view."""

    files_modified: List[ContributorFileSchema] = []
    net_lines: int = 0  # lines_added - lines_deleted


class ProjectContributorsResponse(BaseModel):
    """Schema for project contributors response."""

    project_id: int
    project_name: str
    contributors: List[ContributorSchema] = []
    total_contributors: int = 0
    total_commits: int = 0


class ContributorAnalysisSchema(BaseModel):
    """Schema for contributor analysis with contribution score."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    commits: int = 0
    total_lines_added: int = 0
    total_lines_deleted: int = 0
    net_lines: int = 0  # lines_added - lines_deleted
    files_touched: int = 0  # Number of files modified
    contribution_score: float = 0.0  # 0-100 score
    contribution_percentage: float = 0.0  # Graph visualization: percentage of total contribution
    changes: ChangeStatsSchema = Field(default_factory=ChangeStatsSchema)
    area_scores: dict = Field(default_factory=dict)  # Domain -> percentage (0-100)
    top_paths: List[str] = Field(default_factory=list)
    top_frameworks: List[str] = Field(default_factory=list)


class ProjectContributorsAnalysisResponse(BaseModel):
    """Schema for project contributors analysis response."""

    project_id: int
    project_name: str
    total_contributors: int = 0
    contributors: List[ContributorAnalysisSchema] = []


class AreaShareSchema(BaseModel):
    """Schema for area contribution share."""

    model_config = ConfigDict(from_attributes=True)

    area: str  # "backend", "frontend", "infra", "docs", "devex"
    share: float  # 0-1.0, percentage of total lines changed


class TopFileItemSchema(BaseModel):
    """Schema for top file contribution."""

    model_config = ConfigDict(from_attributes=True)

    file: str  # Relative file path from project root
    lines_changed: int  # lines_added + lines_deleted


class ContributorSummarySchema(BaseModel):
    """Schema for contributor analysis summary."""

    model_config = ConfigDict(from_attributes=True)

    top_areas: List[AreaShareSchema] = []  # Top contributing areas
    top_files: List[TopFileItemSchema] = []  # Top 10 files by lines changed


class ContributorAnalysisDetailSchema(BaseModel):
    """Schema for individual contributor analysis response."""

    model_config = ConfigDict(from_attributes=True)

    contributor_id: int
    name: Optional[str] = None
    summary: ContributorSummarySchema = Field(default_factory=ContributorSummarySchema)


class ContributorAnalysisDetailResponseSchema(BaseModel):
    """Schema for get contributor analysis detail endpoint response."""

    project_id: int
    project_name: str
    branch: str
    contributor: ContributorAnalysisDetailSchema
    generated_at: datetime

