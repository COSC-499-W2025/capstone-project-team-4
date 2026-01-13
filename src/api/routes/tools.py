"""Tools API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.tool import (
    ProjectToolsResponse,
    ToolSummary,
)
from src.repositories.project_repository import ProjectRepository
from src.repositories.tool_repository import ToolRepository
from src.api.exceptions import ProjectNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/tools", tags=["tools"])


@router.get("", response_model=ProjectToolsResponse)
async def get_project_tools(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all tools and technologies detected in a project.

    - Returns tools grouped by category (build, cicd, container, infrastructure, testing, linting, etc.)
    - Includes detection confidence and config file information
    """
    project_repo = ProjectRepository(db)
    tool_repo = ToolRepository(db)

    project = project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # Get all tools for the project
    project_tools = tool_repo.get_by_project(project_id)

    # Build tool summaries
    tools = []
    by_category = {}

    for proj_tool in project_tools:
        tool_summary = ToolSummary(
            name=proj_tool.tool.name,
            category=proj_tool.tool.category,
            detection_score=proj_tool.detection_score,
            config_file=proj_tool.config_file,
        )
        tools.append(tool_summary)

        # Group by category
        category = proj_tool.tool.category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tool_summary)

    # Get category counts
    category_counts = tool_repo.count_by_category(project_id)

    return ProjectToolsResponse(
        project_id=project_id,
        project_name=project.name,
        tools=tools,
        by_category=by_category,
        category_counts=category_counts,
        total_count=len(tools),
    )


@router.get("/category/{category}")
async def get_tools_by_category(
    project_id: int,
    category: str,
    db: Session = Depends(get_db),
):
    """
    Get tools filtered by category.

    - Supported categories: build, cicd, container, infrastructure, testing, linting, package_manager, documentation, deployment, monorepo
    """
    project_repo = ProjectRepository(db)
    tool_repo = ToolRepository(db)

    project = project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    project_tools = tool_repo.get_by_category(project_id, category)

    tools = []
    for proj_tool in project_tools:
        tools.append(ToolSummary(
            name=proj_tool.tool.name,
            category=proj_tool.tool.category,
            detection_score=proj_tool.detection_score,
            config_file=proj_tool.config_file,
        ))

    return {
        "project_id": project_id,
        "category": category,
        "tools": tools,
        "count": len(tools),
    }


@router.get("/categories")
async def get_tool_categories(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all tool categories detected in a project.

    - Returns list of unique category names with counts
    """
    project_repo = ProjectRepository(db)
    tool_repo = ToolRepository(db)

    project = project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    categories = tool_repo.get_categories(project_id)
    counts = tool_repo.count_by_category(project_id)

    return {
        "project_id": project_id,
        "categories": categories,
        "counts": counts,
    }
