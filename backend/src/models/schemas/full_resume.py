"""Pydantic schemas for full resume composition and export."""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ResumeContactInfo(BaseModel):
    """Contact information section of the resume."""

    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class ResumeEducationItem(BaseModel):
    """A single education entry on the resume."""

    institution: str
    degree: str
    field_of_study: str
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    gpa: Optional[Decimal] = None


class ResumeExperienceItem(BaseModel):
    """A single work experience entry on the resume."""

    company_name: str
    job_title: str
    location: Optional[str] = None
    is_remote: bool = False
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    responsibilities: Optional[List[str]] = None
    achievements: Optional[List[str]] = None


class ResumeProjectItem(BaseModel):
    """A single project entry on the resume."""

    title: str
    technologies: List[str] = []
    highlights: List[str] = []
    date_label: Optional[str] = None


class FullResumeData(BaseModel):
    """Complete structured resume data ready for rendering."""

    model_config = ConfigDict(from_attributes=True)

    contact: ResumeContactInfo
    summary: Optional[str] = None
    education: List[ResumeEducationItem] = []
    experience: List[ResumeExperienceItem] = []
    projects: List[ResumeProjectItem] = []
    skills: Dict[str, List[str]] = {}
    generated_at: datetime
