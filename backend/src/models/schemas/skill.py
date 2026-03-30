"""Pydantic schemas for skills."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class SkillSchema(BaseModel):
    """Schema for individual skill."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    category: str
    frequency: int = 1
    source: Optional[str] = None


class SkillWithRelations(SkillSchema):
    """Schema for skill with related entities."""

    related_libraries: List[str] = []
    related_tools: List[str] = []
    related_frameworks: List[str] = []


class SkillCategory(BaseModel):
    """Schema for skills grouped by category."""

    category: str
    skills: List[SkillSchema]
    total_count: int


class SkillSourceBreakdown(BaseModel):
    """Breakdown of skills by source type."""

    from_languages: List[SkillSchema] = []
    from_frameworks: List[SkillSchema] = []
    from_libraries: List[SkillSchema] = []
    from_tools: List[SkillSchema] = []
    contextual: List[SkillSchema] = []
    from_file_types: List[SkillSchema] = []


class ProjectSkillsResponse(BaseModel):
    """Schema for project skills response."""

    project_id: int
    project_name: str
    skills: List[str] = []
    total_skills: int = 0


class SkillSourceResponse(BaseModel):
    """Response for skill sources endpoint."""

    project_id: int
    breakdown: SkillSourceBreakdown
    source_counts: Dict[str, int] = {}


class SkillsBySourceResponse(BaseModel):
    """Response for skills filtered by source."""

    project_id: int
    source: str
    skills: List[SkillSchema]
    total: int


class SkillTimelineEntry(BaseModel):
    """Schema for skill timeline entry."""

    skill: str
    date: str
    count: int


class SkillTimelineResponse(BaseModel):
    """Schema for skill timeline response."""

    project_id: int
    timeline: List[SkillTimelineEntry] = []