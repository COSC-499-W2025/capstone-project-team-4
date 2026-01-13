"""Pydantic schemas for libraries."""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class LibrarySchema(BaseModel):
    """Schema for individual library."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ecosystem: str
    version: Optional[str] = None
    is_dev_dependency: bool = False
    detection_score: float = 1.0


class LibrarySummary(BaseModel):
    """Schema for library summary (without id)."""

    name: str
    ecosystem: str
    version: Optional[str] = None
    is_dev_dependency: bool = False


class LibraryByEcosystem(BaseModel):
    """Schema for libraries grouped by ecosystem."""

    ecosystem: str
    libraries: List[LibrarySummary]
    count: int


class ProjectLibrariesResponse(BaseModel):
    """Schema for project libraries response."""

    project_id: int
    project_name: str
    libraries: List[LibrarySummary]
    by_ecosystem: Dict[str, List[LibrarySummary]] = {}
    ecosystem_counts: Dict[str, int] = {}
    total_count: int = 0
    dev_dependency_count: int = 0
    production_dependency_count: int = 0


class LibraryDetectionResult(BaseModel):
    """Schema for library detection result from extractor."""

    name: str
    version: Optional[str] = None
    ecosystem: str
    is_dev_dependency: bool = False
