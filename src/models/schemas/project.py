"""Pydantic schemas for projects."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """Base project schema."""

    name: str = Field(..., min_length=1, max_length=255)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    root_path: str
    source_type: str = "local"
    source_url: Optional[str] = None


class ProjectSummary(ProjectBase):
    """Schema for project summary in list views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: str
    created_at: datetime
    file_count: int = 0
    language_count: int = 0
    framework_count: int = 0
    contributor_count: int = 0
    skill_count: int = 0


class ProjectDetail(ProjectSummary):
    """Schema for detailed project view."""

    root_path: str
    source_url: Optional[str] = None
    updated_at: datetime
    languages: List[str] = []
    frameworks: List[str] = []
    total_lines_of_code: int = 0
    avg_complexity: float = 0.0
    max_complexity: int = 0


class ProjectList(BaseModel):
    """Schema for paginated project list."""

    items: List[ProjectSummary]
    total: int
    page: int
    page_size: int
    pages: int
