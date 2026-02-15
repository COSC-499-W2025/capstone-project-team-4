"""Contributor repository for database operations."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.models.orm.contributor import Contributor, ContributorFile
from src.repositories.base import BaseRepository


class ContributorRepository(BaseRepository[Contributor]):
    """Repository for contributor operations."""

    def __init__(self, db: Session):
        """Initialize contributor repository."""
        super().__init__(Contributor, db)

    def get_by_project(self, project_id: int) -> List[Contributor]:
        """Get all contributors for a project."""
        stmt = (
            select(Contributor)
            .where(Contributor.project_id == project_id)
            .order_by(Contributor.percent.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_with_files(self, contributor_id: int) -> Optional[Contributor]:
        """Get contributor with file modifications loaded."""
        stmt = (
            select(Contributor)
            .options(joinedload(Contributor.files_modified))
            .where(Contributor.id == contributor_id)
        )
        return self.db.scalar(stmt)

    def get_top_contributor(self, project_id: int) -> Optional[Contributor]:
        """Get the top contributor by commit percentage."""
        stmt = (
            select(Contributor)
            .where(Contributor.project_id == project_id)
            .order_by(Contributor.percent.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def create_contributor(
        self,
        project_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        github_username: Optional[str] = None,
        github_email: Optional[str] = None,
        commits: int = 0,
        percent: float = 0.0,
        total_lines_added: int = 0,
        total_lines_deleted: int = 0,
    ) -> Contributor:
        """Create a new contributor."""
        contributor = Contributor(
            project_id=project_id,
            name=name,
            email=email,
            github_username=github_username,
            github_email=github_email,
            commits=commits,
            percent=percent,
            total_lines_added=total_lines_added,
            total_lines_deleted=total_lines_deleted,
        )
        return self.create(contributor)

    def create_contributor_file(
        self,
        contributor_id: int,
        filename: str,
        modifications: int = 0,
    ) -> ContributorFile:
        """Create a contributor file modification record."""
        cf = ContributorFile(
            contributor_id=contributor_id,
            filename=filename,
            modifications=modifications,
        )
        self.db.add(cf)
        self.db.commit()
        self.db.refresh(cf)
        return cf

    def create_contributors_bulk(self, contributors_data: List[dict]) -> List[Contributor]:
        """Create multiple contributors efficiently."""
        contributors = []
        for data in contributors_data:
            contributor = Contributor(
                project_id=data["project_id"],
                name=data.get("name"),
                email=data.get("email"),
                github_username=data.get("github_username"),
                github_email=data.get("github_email"),
                commits=data.get("commits", 0),
                percent=data.get("percent", 0.0),
                total_lines_added=data.get("total_lines_added", 0),
                total_lines_deleted=data.get("total_lines_deleted", 0),
            )
            contributors.append(contributor)

        if not contributors:
            return []

        self.db.add_all(contributors)
        self.db.flush()

        # Create file modifications for each contributor in bulk
        contributor_files = []
        for i, data in enumerate(contributors_data):
            files_modified = data.get("files_modified") or []
            for file_data in files_modified:
                contributor_files.append(
                    ContributorFile(
                        contributor_id=contributors[i].id,
                        filename=file_data.get("filename", ""),
                        modifications=file_data.get("modifications", 0),
                    )
                )

        if contributor_files:
            self.db.add_all(contributor_files)

        self.db.commit()
        for contributor in contributors:
            self.db.refresh(contributor)

        return contributors

    def delete_by_project_id(self, project_id: int) -> int:
        """Delete all contributors for a project."""
        # Delete contributor files first
        stmt_files = select(ContributorFile).where(
            ContributorFile.contributor_id.in_(
                select(Contributor.id).where(Contributor.project_id == project_id)
            )
        )
        for file_obj in self.db.scalars(stmt_files):
            self.db.delete(file_obj)
        
        # Delete contributors
        stmt = select(Contributor).where(Contributor.project_id == project_id)
        count = 0
        for contributor in self.db.scalars(stmt):
            self.db.delete(contributor)
            count += 1
        
        self.db.commit()
        return count

    def count_by_project(self, project_id: int) -> int:
        """Count contributors in a project."""
        stmt = select(func.count(Contributor.id)).where(Contributor.project_id == project_id)
        return self.db.scalar(stmt) or 0

    def get_total_commits(self, project_id: int) -> int:
        """Get total commits for a project."""
        result = self.db.scalar(
            select(func.sum(Contributor.commits)).where(Contributor.project_id == project_id)
        )
        return result or 0
