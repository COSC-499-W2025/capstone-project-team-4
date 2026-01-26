"""Pydantic schemas for analysis."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AnalysisStatus(str, Enum):
    """Analysis status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisRequest(BaseModel):
    """Base analysis request schema."""

    project_name: Optional[str] = Field(None, min_length=1, max_length=255)


class GitHubAnalysisRequest(AnalysisRequest):
    """Schema for GitHub repository analysis."""

    github_url: HttpUrl
    branch: Optional[str] = None


class ComplexitySummary(BaseModel):
    """Summary of complexity metrics."""

    total_functions: int = 0
    avg_complexity: float = 0.0
    max_complexity: int = 0
    high_complexity_count: int = 0  # Functions with complexity > 10


class AnalysisResult(BaseModel):
    """Schema for analysis result."""

    project_id: int
    project_name: str
    status: AnalysisStatus
    source_type: str
    source_url: Optional[str] = None
    languages: List[str] = []
    frameworks: List[str] = []
    libraries: List[str] = []
    tools_and_technologies: List[str] = []
    contextual_skills: List[str] = []
    file_count: int = 0
    contributor_count: int = 0
    skill_count: int = 0
    library_count: int = 0
    tool_count: int = 0
    total_lines_of_code: int = 0
    complexity_summary: Optional[ComplexitySummary] = None
    zip_uploaded_at: datetime
    first_file_created: datetime
    first_commit_date: Optional[datetime] = None
    project_started_at: datetime
    error_message: Optional[str] = None
