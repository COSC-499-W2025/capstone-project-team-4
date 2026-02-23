"""Project repository for database operations."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.models.orm.project import Project
from src.models.orm.file import File, Language
from src.models.orm.skill import ProjectSkill
from src.models.orm.framework import ProjectFramework, Framework
from src.models.orm.library import ProjectLibrary, Library
from src.models.orm.tool import ProjectTool, Tool
from src.models.orm.contributor import Contributor
from src.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for project operations."""

    def __init__(self, db: Session):
        """Initialize project repository."""
        super().__init__(Project, db)

    def get_with_relations(self, project_id: int) -> Optional[Project]:
        """Get project with all related data loaded."""
        stmt = (
            select(Project)
            .options(
                joinedload(Project.files),
                joinedload(Project.contributors),
                joinedload(Project.skills),
                joinedload(Project.resume_items),
                joinedload(Project.frameworks).joinedload(ProjectFramework.framework),
            )
            .where(Project.id == project_id)
        )
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Optional[Project]:
        """Get project by name."""
        stmt = select(Project).where(Project.name == name)
        return self.db.scalar(stmt)
    
    def get_latest_by_analysis_key(self, analysis_key: str) -> Optional[Project]:
        """Get most recent project with the given analysis_key (for cache reuse)."""
        stmt = (
            select(Project)
            .where(Project.analysis_key == analysis_key)
            .order_by(Project.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_summary(self, project_id: int) -> Optional[dict]:
        """Get project summary with counts."""
        project = self.get(project_id)
        if not project:
            return None
    
        # Get counts
        file_count = self.db.scalar(
            select(func.count(File.id)).where(File.project_id == project_id)
        ) or 0

        contributor_count = self.db.scalar(
            select(func.count(Contributor.id)).where(Contributor.project_id == project_id)
        ) or 0

        skill_count = self.db.scalar(
            select(func.count(ProjectSkill.id)).where(ProjectSkill.project_id == project_id)
        ) or 0

        framework_count = self.db.scalar(
            select(func.count(ProjectFramework.id)).where(ProjectFramework.project_id == project_id)
        ) or 0

        # Get unique languages count
        language_count = self.db.scalar(
            select(func.count(func.distinct(File.language_id)))
            .where(File.project_id == project_id)
            .where(File.language_id.isnot(None))
        ) or 0
        
        tool_count = self.db.scalar(
            select(func.count(ProjectTool.id)).where(ProjectTool.project_id == project_id)
        ) or 0
        
        library_count = self.db.scalar(
            select(func.count(ProjectLibrary.id)).where(ProjectLibrary.project_id == project_id)
        ) or 0

        return {
            "id": project.id,
            "name": project.name,
            "source_type": project.source_type,
            "created_at": project.created_at,
            "zip_uploaded_at": project.zip_uploaded_at,
            "first_file_created": project.first_file_created,
            "first_commit_date": project.first_commit_date,
            "project_started_at": project.project_started_at,
            "file_count": file_count,
            "contributor_count": contributor_count,
            "skill_count": skill_count,
            "framework_count": framework_count,
            "language_count": language_count,
            "tool_count": tool_count,
            "library_count": library_count,
        }

    def get_all_summaries(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all project summaries (bulk). Avoid N+1 count queries."""
        # Fetch the base projects first
        projects = self.get_all(skip=skip, limit=limit)
        if not projects:
            return []

        project_ids = [p.id for p in projects]

        # Bulk counts grouped by project_id
        file_counts = dict(
            self.db.execute(
                select(File.project_id, func.count(File.id))
                .where(File.project_id.in_(project_ids))
                .group_by(File.project_id)
            ).all()
        )

        contributor_counts = dict(
            self.db.execute(
                select(Contributor.project_id, func.count(Contributor.id))
                .where(Contributor.project_id.in_(project_ids))
                .group_by(Contributor.project_id)
            ).all()
        )

        skill_counts = dict(
            self.db.execute(
                select(ProjectSkill.project_id, func.count(ProjectSkill.id))
                .where(ProjectSkill.project_id.in_(project_ids))
                .group_by(ProjectSkill.project_id)
            ).all()
        )

        framework_counts = dict(
            self.db.execute(
                select(ProjectFramework.project_id, func.count(ProjectFramework.id))
                .where(ProjectFramework.project_id.in_(project_ids))
                .group_by(ProjectFramework.project_id)
            ).all()
        )

        language_counts = dict(
            self.db.execute(
                select(File.project_id, func.count(func.distinct(File.language_id)))
                .where(File.project_id.in_(project_ids))
                .where(File.language_id.isnot(None))
                .group_by(File.project_id)
            ).all()
        )

        tool_counts = dict(
            self.db.execute(
                select(ProjectTool.project_id, func.count(ProjectTool.id))
                .where(ProjectTool.project_id.in_(project_ids))
                .group_by(ProjectTool.project_id)
            ).all()
        )

        library_counts = dict(
            self.db.execute(
                select(ProjectLibrary.project_id, func.count(ProjectLibrary.id))
                .where(ProjectLibrary.project_id.in_(project_ids))
                .group_by(ProjectLibrary.project_id)
            ).all()
        )

        # Build summaries in the same shape as get_summary()
        summaries: List[dict] = []
        for p in projects:
            pid = p.id
            summaries.append(
                {
                    "id": pid,
                    "name": p.name,
                    "source_type": p.source_type,
                    "created_at": p.created_at,
                    "zip_uploaded_at": p.zip_uploaded_at,
                    "first_file_created": p.first_file_created,
                    "first_commit_date": p.first_commit_date,
                    "project_started_at": p.project_started_at,
                    "file_count": int(file_counts.get(pid, 0)),
                    "contributor_count": int(contributor_counts.get(pid, 0)),
                    "skill_count": int(skill_counts.get(pid, 0)),
                    "framework_count": int(framework_counts.get(pid, 0)),
                    "language_count": int(language_counts.get(pid, 0)),
                    "tool_count": int(tool_counts.get(pid, 0)),
                    "library_count": int(library_counts.get(pid, 0)),
                }
            )

        return summaries

    def create_project(
        self,
        name: str,
        root_path: str,
        source_type: str = "local",
        source_url: Optional[str] = None,
        zip_uploaded_at: Optional[datetime] = None,
        first_file_created: Optional[datetime] = None,
        first_commit_date: Optional[datetime] = None,
        project_started_at: Optional[datetime] = None,
        content_hash: Optional[str] = None,
        analysis_key: Optional[str] = None,
        reused_from_project_id: Optional[int] = None,
    ) -> Project:
        """Create a new project."""
        project = Project(
            name=name,
            root_path=root_path,
            source_type=source_type,
            source_url=source_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            zip_uploaded_at=zip_uploaded_at,
            first_file_created=first_file_created,
            first_commit_date=first_commit_date,
            project_started_at=project_started_at,
            content_hash=content_hash,
            analysis_key=analysis_key,
            reused_from_project_id=reused_from_project_id,
        )
        return self.create(project)

    def get_languages(self, project_id: int) -> List[str]:
        """Get all unique languages for a project."""
        stmt = (
            select(Language.name)
            .join(File, File.language_id == Language.id)
            .where(File.project_id == project_id)
            .distinct()
        )
        return list(self.db.scalars(stmt).all())

    def update_timestamps(
        self,
        project_id: int,
        zip_uploaded_at: Optional[datetime],
        first_file_created: Optional[datetime],
        first_commit_date: Optional[datetime],
        project_started_at: Optional[datetime],
    ) -> Optional[Project]:
        """Persist timestamp fields on project."""
        project = self.get(project_id)
        if not project:
            return None

        project.zip_uploaded_at = zip_uploaded_at
        project.first_file_created = first_file_created
        project.first_commit_date = first_commit_date
        project.project_started_at = project_started_at
        return self.update(project)

    def get_frameworks(self, project_id: int) -> List[str]:
        """Get all frameworks for a project."""
        stmt = (
            select(Framework.name)
            .join(ProjectFramework, ProjectFramework.framework_id == Framework.id)
            .where(ProjectFramework.project_id == project_id)
        )
        return list(self.db.scalars(stmt).all())

    def get_libraries(self, project_id: int) -> List[str]:
        """Get all libraries for a project."""
        stmt = (
            select(Library.name)
            .join(ProjectLibrary, ProjectLibrary.library_id == Library.id)
            .where(ProjectLibrary.project_id == project_id)
        )
        return list(self.db.scalars(stmt).all())

    def get_tools(self, project_id: int) -> List[str]:
        """Get all tools for a project."""
        stmt = (
            select(Tool.name)
            .join(ProjectTool, ProjectTool.tool_id == Tool.id)
            .where(ProjectTool.project_id == project_id)
        )
        return list(self.db.scalars(stmt).all())

    def get_total_lines_of_code(self, project_id: int) -> int:
        """Get total lines of code for a project."""
        result = self.db.scalar(
            select(func.sum(File.lines_of_code)).where(File.project_id == project_id)
        )
        return result or 0
