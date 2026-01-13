"""Pydantic schemas for resume items."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ResumeItemBase(BaseModel):
    """Base resume item schema."""

    title: str = Field(..., min_length=1, max_length=500)
    highlights: List[str] = []


class ResumeItemCreate(ResumeItemBase):
    """Schema for creating a resume item."""

    project_id: int


class ResumeItemSchema(BaseModel):
    """Schema for resume item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str = Field(..., min_length=1, max_length=500)
    highlights: List[str] = []
    created_at: datetime


class ResumeItemUpdate(BaseModel):
    """Schema for updating a resume item."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    highlights: Optional[List[str]] = None


class ProjectResumeResponse(BaseModel):
    """Schema for project resume response."""

    project_id: int
    project_name: str
    resume_items: List[ResumeItemSchema] = []
