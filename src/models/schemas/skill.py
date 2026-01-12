"""Pydantic schemas for skills."""

from typing import Dict, List

from pydantic import BaseModel, ConfigDict


class SkillSchema(BaseModel):
    """Schema for individual skill."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    category: str
    frequency: int = 1


class SkillCategory(BaseModel):
    """Schema for skills grouped by category."""

    category: str
    skills: List[SkillSchema]
    total_count: int


class ProjectSkillsResponse(BaseModel):
    """Schema for project skills response."""

    project_id: int
    project_name: str
    languages: List[str] = []
    frameworks: List[str] = []
    skills_by_category: Dict[str, List[SkillSchema]] = {}
    total_skills: int = 0
    total_categories: int = 0


class SkillTimelineEntry(BaseModel):
    """Schema for skill timeline entry."""

    skill: str
    date: str
    count: int


class SkillTimelineResponse(BaseModel):
    """Schema for skill timeline response."""

    project_id: int
    timeline: List[SkillTimelineEntry]
