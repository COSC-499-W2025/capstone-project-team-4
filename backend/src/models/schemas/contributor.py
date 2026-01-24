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


class ProjectContributorsAnalysisResponse(BaseModel):
    """Schema for project contributors analysis response."""

    project_id: int
    project_name: str
    total_contributors: int = 0
    contributors: List[ContributorAnalysisSchema] = []
