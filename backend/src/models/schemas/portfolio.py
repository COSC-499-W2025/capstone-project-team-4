"""Pydantic schemas for portfolios."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""

    title: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


class PortfolioResponse(BaseModel):
    """Schema for portfolio response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    summary: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class PortfolioProjectCustomize(BaseModel):
    """Data to customize a specific project inside a portfolio."""

    # Include the generated fields so that the user can also replace them if they want
    name: Optional[str] = None
    languages: Optional[List[str]] = None
    frameworks: Optional[List[str]] = None
    resume_highlights: Optional[List[str]] = None

    # Custom field stuff
    # Next time when working on the frontend we can add any field below to make it match the form on the frontend
    # for now, these 3 will do.
    custom_name: Optional[str] = None
    description: Optional[str] = None
    live_demo_url: Optional[str] = None
    is_featured: Optional[bool] = None
