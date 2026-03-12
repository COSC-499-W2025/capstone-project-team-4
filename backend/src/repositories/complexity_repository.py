"""Complexity repository for database operations."""

from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.orm.complexity import Complexity
from src.repositories.base import BaseRepository


class ComplexityRepository(BaseRepository[Complexity]):
    """Repository for complexity operations."""

    def __init__(self, db: Session):
        """Initialize complexity repository."""
        super().__init__(Complexity, db)

    def get_by_project(
        self, project_id: int, skip: int = 0, limit: int = 1000
    ) -> List[Complexity]:
        """Get all complexity records for a project."""
        stmt = (
            select(Complexity)
            .where(Complexity.project_id == project_id)
            .order_by(Complexity.cyclomatic_complexity.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_high_complexity(
        self, project_id: int, threshold: int = 10
    ) -> List[Complexity]:
        """Get functions with high complexity."""
        stmt = (
            select(Complexity)
            .where(Complexity.project_id == project_id)
            .where(Complexity.cyclomatic_complexity > threshold)
            .order_by(Complexity.cyclomatic_complexity.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_file(self, project_id: int, file_path: str) -> List[Complexity]:
        """Get complexity records for a specific file."""
        stmt = (
            select(Complexity)
            .where(Complexity.project_id == project_id)
            .where(Complexity.file_path == file_path)
            .order_by(Complexity.start_line)
        )
        return list(self.db.scalars(stmt).all())

    def get_summary(self, project_id: int) -> Dict:
        """Get complexity summary statistics for a project."""
        stmt = select(Complexity).where(Complexity.project_id == project_id)
        complexities = list(self.db.scalars(stmt).all())

        if not complexities:
            return {
                "total_functions": 0,
                "avg_complexity": 0.0,
                "max_complexity": 0,
                "min_complexity": 0,
                "high_complexity_count": 0,
                "medium_complexity_count": 0,
                "low_complexity_count": 0,
            }

        complexity_values = [c.cyclomatic_complexity for c in complexities]

        return {
            "total_functions": len(complexities),
            "avg_complexity": sum(complexity_values) / len(complexity_values),
            "max_complexity": max(complexity_values),
            "min_complexity": min(complexity_values),
            "high_complexity_count": len([c for c in complexity_values if c > 10]),
            "medium_complexity_count": len(
                [c for c in complexity_values if 5 <= c <= 10]
            ),
            "low_complexity_count": len([c for c in complexity_values if c < 5]),
        }

    def get_by_file_grouped(self, project_id: int) -> Dict[str, List[Complexity]]:
        """Get complexity records grouped by file."""
        complexities = self.get_by_project(project_id, limit=10000)
        grouped = {}
        for c in complexities:
            if c.file_path not in grouped:
                grouped[c.file_path] = []
            grouped[c.file_path].append(c)
        return grouped

    def create_complexity(
        self,
        project_id: int,
        file_path: str,
        function_name: str,
        cyclomatic_complexity: int = 1,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> Complexity:
        """Create a new complexity record."""
        complexity = Complexity(
            project_id=project_id,
            file_path=file_path,
            function_name=function_name,
            cyclomatic_complexity=cyclomatic_complexity,
            start_line=start_line,
            end_line=end_line,
        )
        return self.create(complexity)

    def create_complexities_bulk(
        self, project_id: int, complexity_data: List[dict]
    ) -> List[Complexity]:
        """Create multiple complexity records efficiently."""
        complexities = []
        for data in complexity_data:
            complexity = Complexity(
                project_id=project_id,
                file_path=data["file_path"],
                function_name=data["function_name"],
                cyclomatic_complexity=data.get("cyclomatic_complexity", 1),
                start_line=data.get("start_line"),
                end_line=data.get("end_line"),
            )
            complexities.append(complexity)
        return self.create_many(complexities)

    def count_by_project(self, project_id: int) -> int:
        """Count complexity records in a project."""
        stmt = select(func.count(Complexity.id)).where(
            Complexity.project_id == project_id
        )
        return self.db.scalar(stmt) or 0

    def get_by_project_and_paths(
        self, project_id: int, paths: set[str]
    ) -> list[Complexity]:
        if not paths:
            return []
        stmt = (
            select(Complexity)
            .where(Complexity.project_id == project_id)
            .where(Complexity.file_path.in_(list(paths)))
        )
        return list(self.db.scalars(stmt).all())

    def bulk_create_from_dicts(self, rows: list[dict]) -> None:
        if not rows:
            return
        self.db.bulk_insert_mappings(Complexity, rows)
        self.db.commit()
