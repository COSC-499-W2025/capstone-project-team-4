"""Tool repository for database operations."""

from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.orm.tool import Tool, ProjectTool
from src.repositories.base import BaseRepository


class ToolRepository(BaseRepository[ProjectTool]):
    """Repository for tool operations."""

    def __init__(self, db: Session):
        """Initialize tool repository."""
        super().__init__(ProjectTool, db)

    def get_or_create_tool(self, name: str, category: str) -> Tool:
        """Get existing tool or create a new one."""
        stmt = select(Tool).where(Tool.name == name)
        existing = self.db.scalar(stmt)
        if existing:
            return existing

        tool = Tool(name=name, category=category)
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        return tool

    def get_by_project(self, project_id: int) -> List[ProjectTool]:
        """Get all tools for a project."""
        stmt = (
            select(ProjectTool)
            .where(ProjectTool.project_id == project_id)
            .order_by(ProjectTool.tool_id)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_category(self, project_id: int, category: str) -> List[ProjectTool]:
        """Get tools by category for a project."""
        stmt = (
            select(ProjectTool)
            .join(Tool)
            .where(ProjectTool.project_id == project_id)
            .where(Tool.category == category)
        )
        return list(self.db.scalars(stmt).all())

    def get_grouped_by_category(self, project_id: int) -> Dict[str, List[ProjectTool]]:
        """Get tools grouped by category."""
        tools = self.get_by_project(project_id)
        grouped: Dict[str, List[ProjectTool]] = {}
        for proj_tool in tools:
            category = proj_tool.tool.category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(proj_tool)
        return grouped

    def get_categories(self, project_id: int) -> List[str]:
        """Get all unique categories for a project."""
        stmt = (
            select(Tool.category)
            .join(ProjectTool)
            .where(ProjectTool.project_id == project_id)
            .distinct()
        )
        return list(self.db.scalars(stmt).all())

    def create_project_tool(
        self,
        project_id: int,
        tool_id: int,
        detection_score: float = 1.0,
        config_file: Optional[str] = None,
    ) -> ProjectTool:
        """Create a new project tool association."""
        # Check if association already exists
        existing = self.db.scalar(
            select(ProjectTool)
            .where(ProjectTool.project_id == project_id)
            .where(ProjectTool.tool_id == tool_id)
        )
        if existing:
            # Update score if higher
            if detection_score > existing.detection_score:
                existing.detection_score = detection_score
            if config_file:
                existing.config_file = config_file
            self.db.commit()
            self.db.refresh(existing)
            return existing

        project_tool = ProjectTool(
            project_id=project_id,
            tool_id=tool_id,
            detection_score=detection_score,
            config_file=config_file,
        )
        return self.create(project_tool)

    def create_tools_bulk(
        self, tools_data: List[dict], project_id: int
    ) -> List[ProjectTool]:
        """Create multiple tools efficiently."""
        project_tools = []
        seen = set()

        for data in tools_data:
            name = data.get("name", "").strip()
            if not name:
                continue

            # Deduplicate by name within this batch
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)

            # Get or create the tool lookup record
            tool = self.get_or_create_tool(
                name=name, category=data.get("category", "other")
            )

            # Check if project-tool association exists
            existing = self.db.scalar(
                select(ProjectTool)
                .where(ProjectTool.project_id == project_id)
                .where(ProjectTool.tool_id == tool.id)
            )
            if existing:
                continue

            project_tool = ProjectTool(
                project_id=project_id,
                tool_id=tool.id,
                detection_score=data.get("confidence", 1.0),
                config_file=data.get("config_file"),
            )
            project_tools.append(project_tool)

        if project_tools:
            return self.create_many(project_tools)
        return []

    def count_by_project(self, project_id: int) -> int:
        """Count tools in a project."""
        stmt = select(func.count(ProjectTool.id)).where(
            ProjectTool.project_id == project_id
        )
        return self.db.scalar(stmt) or 0

    def count_by_category(self, project_id: int) -> Dict[str, int]:
        """Count tools by category for a project."""
        stmt = (
            select(Tool.category, func.count(ProjectTool.id))
            .join(Tool)
            .where(ProjectTool.project_id == project_id)
            .group_by(Tool.category)
        )
        result = self.db.execute(stmt).all()
        return {row[0]: row[1] for row in result}

    def delete_by_project(self, project_id: int) -> int:
        """Delete all tools for a project."""
        stmt = select(ProjectTool).where(ProjectTool.project_id == project_id)
        tools = list(self.db.scalars(stmt).all())
        count = len(tools)
        for tool in tools:
            self.db.delete(tool)
        self.db.commit()
        return count

    def get_tool_names(self, project_id: int) -> List[str]:
        """Get all tool names for a project."""
        stmt = (
            select(Tool.name)
            .join(ProjectTool)
            .where(ProjectTool.project_id == project_id)
            .order_by(Tool.name)
        )
        return list(self.db.scalars(stmt).all())

    def get_tools_by_category_names(self, project_id: int) -> Dict[str, List[str]]:
        """Get tool names grouped by category."""
        stmt = (
            select(Tool.category, Tool.name)
            .join(ProjectTool)
            .where(ProjectTool.project_id == project_id)
            .order_by(Tool.category, Tool.name)
        )
        result = self.db.execute(stmt).all()
        grouped: Dict[str, List[str]] = {}
        for category, name in result:
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(name)
        return grouped
