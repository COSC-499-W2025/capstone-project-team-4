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
