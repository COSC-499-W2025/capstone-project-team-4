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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "project_id": 1,
                "project_name": "example-project",
                "status": "completed",
                "source_type": "zip",
                "source_url": "/path/to/project.zip",
                "languages": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "React"],
                "tools_and_technologies": ["Docker", "Git"],
                "contextual_skills": ["REST", "CI/CD"],
                "file_count": 120,
                "contributor_count": 3,
                "skill_count": 25,
                "library_count": 10,
                "tool_count": 5,
                "total_lines_of_code": 15432,
                "complexity_summary": {
                    "total_functions": 220,
                    "avg_complexity": 3.2,
                    "max_complexity": 18,
                    "high_complexity_count": 12
                },
                "zip_uploaded_at": "2026-01-18T12:00:00Z",
                "first_file_created": "2024-05-10T09:30:00Z",
                "first_commit_date": "2024-05-11T10:00:00Z",
                "project_started_at": "2024-05-10T09:30:00Z",
            }
        },
    )

    project_id: int
    project_name: str
    status: AnalysisStatus
    source_type: str
    source_url: Optional[str] = None
    languages: List[str] = []
    frameworks: List[str] = []
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
