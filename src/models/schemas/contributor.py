"""Pydantic schemas for contributors."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ContributorFileSchema(BaseModel):
    """Schema for contributor file modifications."""

    model_config = ConfigDict(from_attributes=True)

    filename: str
    modifications: int


class ContributorSchema(BaseModel):
    """Schema for contributor summary."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    commits: int = 0
    percent: float = 0.0
    total_lines_added: int = 0
    total_lines_deleted: int = 0


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
