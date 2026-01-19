"""Pydantic schemas for tools and technologies."""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ToolSchema(BaseModel):
    """Schema for individual tool."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    detection_score: float = 1.0
    config_file: Optional[str] = None


class ToolSummary(BaseModel):
    """Schema for tool summary (without id)."""

    name: str
    category: str
    detection_score: float = 1.0
    config_file: Optional[str] = None


class ToolByCategory(BaseModel):
    """Schema for tools grouped by category."""

    category: str
    tools: List[ToolSummary]
    count: int


class ProjectToolsResponse(BaseModel):
    """Schema for project tools response."""

    project_id: int
    project_name: str
    tools: List[ToolSummary]
    by_category: Dict[str, List[ToolSummary]] = {}
    category_counts: Dict[str, int] = {}
    total_count: int = 0


class ToolDetectionResult(BaseModel):
    """Schema for tool detection result from extractor."""

    name: str
    category: str
    confidence: float = 1.0
    config_file: Optional[str] = None
    signals: List[str] = []
