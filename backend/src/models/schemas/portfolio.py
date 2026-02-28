"""Pydantic schemas for portfolios."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field


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
    custom_name: Optional[str] = None
    description: Optional[str] = None
    live_demo_url: Optional[str] = None
    # Next time when working on the frontend we can add any field below to make it match the form on the frontend
    # for now, these 3 up above will do.