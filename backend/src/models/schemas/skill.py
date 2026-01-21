"""Pydantic schemas for skills."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class SkillSchema(BaseModel):
    """Schema for individual skill."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    category: str
    frequency: int = 1
    # Source tracking fields for complementary detection system
    source: Optional[str] = None
    source_id: Optional[int] = None
    cross_validation_boost: Optional[float] = None


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


class CrossValidationSummary(BaseModel):
    """Summary of cross-validation results."""

    total_frameworks: int = 0
    original_frameworks: int = 0
    gap_filled_frameworks: int = 0
    frameworks_boosted: int = 0
    frameworks_penalized: int = 0
    validation_sources_used: Dict[str, int] = {}


class ProjectSkillsResponse(BaseModel):
    """Schema for project skills response."""

    project_id: int
    project_name: str
    languages: List[str] = []
    frameworks: List[str] = []
    libraries: List[str] = []
    tools: List[str] = []
    total_skills: int = 0
    # New fields for complementary detection system
    skill_sources: Optional[SkillSourceBreakdown] = None
    cross_validation_summary: Optional[CrossValidationSummary] = None


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
    timeline: List[SkillTimelineEntry]


class CrossValidationResponse(BaseModel):
    """Response for cross-validation endpoint."""

    project_id: int
    summary: CrossValidationSummary
    enhanced_frameworks: List[Dict[str, Any]] = []
    gap_filled_frameworks: List[Dict[str, Any]] = []
