"""Pydantic schemas for education entries."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EducationBase(BaseModel):
    """Base education schema with shared fields."""

    institution: str = Field(..., min_length=1, max_length=255)
    degree: str = Field(..., min_length=1, max_length=255)
    field_of_study: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    honors: Optional[str] = None
    activities: Optional[str] = None


class EducationCreate(EducationBase):
    """Schema for creating an education entry."""

    pass


class EducationUpdate(BaseModel):
    """Schema for updating an education entry. All fields optional."""

    institution: Optional[str] = Field(None, min_length=1, max_length=255)
    degree: Optional[str] = Field(None, min_length=1, max_length=255)
    field_of_study: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    honors: Optional[str] = None
    activities: Optional[str] = None


class EducationResponse(EducationBase):
    """Schema for education response with id and timestamps."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
