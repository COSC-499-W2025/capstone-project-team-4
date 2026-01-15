"""Pydantic schemas for user profiles."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


# Work Experience Schemas
class WorkExperienceBase(BaseModel):
    """Base work experience schema."""

    company_name: str = Field(..., min_length=1, max_length=255)
    job_title: str = Field(..., min_length=1, max_length=255)
    employment_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    is_remote: bool = False
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    achievements: Optional[List[str]] = None


class WorkExperienceCreate(WorkExperienceBase):
    """Schema for creating a work experience entry."""

    pass


class WorkExperienceUpdate(BaseModel):
    """Schema for updating a work experience entry."""

    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    job_title: Optional[str] = Field(None, min_length=1, max_length=255)
    employment_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    is_remote: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    achievements: Optional[List[str]] = None


class WorkExperienceResponse(WorkExperienceBase):
    """Schema for work experience response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_profile_id: int
    created_at: datetime
    updated_at: datetime


# User Profile Schemas
class UserProfileBase(BaseModel):
    """Base user profile schema."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    portfolio_url: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    """Schema for creating a user profile."""

    work_experiences: Optional[List[WorkExperienceCreate]] = None


class UserProfileUpdate(BaseModel):
    """Schema for updating a user profile."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    portfolio_url: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None


class UserProfileSummary(UserProfileBase):
    """Schema for user profile summary."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class UserProfileDetail(UserProfileSummary):
    """Schema for detailed user profile view with work experiences."""

    updated_at: datetime
    work_experiences: List[WorkExperienceResponse] = []


class UserProfileList(BaseModel):
    """Schema for paginated user profile list."""

    items: List[UserProfileSummary]
    total: int
    page: int
    page_size: int
    pages: int
