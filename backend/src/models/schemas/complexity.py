"""Pydantic schemas for complexity metrics."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ComplexitySchema(BaseModel):
    """Schema for function complexity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    function_name: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    cyclomatic_complexity: int = 1


class ComplexitySummary(BaseModel):
    """Schema for complexity summary statistics."""

    total_functions: int = 0
    avg_complexity: float = 0.0
    max_complexity: int = 0
    min_complexity: int = 0
    high_complexity_count: int = 0  # complexity > 10
    medium_complexity_count: int = 0  # complexity 5-10
    low_complexity_count: int = 0  # complexity < 5


class ComplexityByFile(BaseModel):
    """Schema for complexity grouped by file."""

    file_path: str
    function_count: int
    avg_complexity: float
    max_complexity: int
    functions: List[ComplexitySchema] = []


class ComplexityReport(BaseModel):
    """Schema for full complexity report."""

    project_id: int
    project_name: str
    summary: ComplexitySummary
    by_file: List[ComplexityByFile] = []
    high_complexity_functions: List[ComplexitySchema] = []
