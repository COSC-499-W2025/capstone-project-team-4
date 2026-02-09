"""File repository for database operations."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.orm.file import File, Language
from src.repositories.base import BaseRepository


class FileRepository(BaseRepository[File]):
    """Repository for file operations."""

    def __init__(self, db: Session):
        """Initialize file repository."""
        super().__init__(File, db)

    def get_by_project(self, project_id: int, skip: int = 0, limit: int = 1000) -> List[File]:
        """Get all files for a project."""
        stmt = (
            select(File)
            .where(File.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_language(self, project_id: int, language_name: str) -> List[File]:
        """Get files by language for a project."""
        stmt = (
            select(File)
            .join(Language, File.language_id == Language.id)
            .where(File.project_id == project_id)
            .where(Language.name == language_name)
        )
        return list(self.db.scalars(stmt).all())

    def get_or_create_language(self, language_name: str) -> Language:
        """Get or create a language record."""
        stmt = select(Language).where(Language.name == language_name)
        language = self.db.scalar(stmt)
        if not language:
            language = Language(name=language_name)
            self.db.add(language)
            self.db.commit()
            self.db.refresh(language)
        return language

    def create_file(
        self,
        project_id: int,
        path: str,
        language_name: Optional[str] = None,
        file_size: Optional[int] = None,
        lines_of_code: Optional[int] = None,
        comment_lines: Optional[int] = None,
        blank_lines: Optional[int] = None,
        created_timestamp: Optional[float] = None,
        last_modified: Optional[float] = None,
        content_hash: Optional[str] = None,
    ) -> File:
        """Create a new file record."""
        language_id = None
        if language_name:
            language = self.get_or_create_language(language_name)
            language_id = language.id

        file = File(
            project_id=project_id,
            path=path,
            language_id=language_id,
            file_size=file_size,
            lines_of_code=lines_of_code,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            created_timestamp=created_timestamp,
            last_modified=last_modified,
            content_hash=content_hash,
        )
        return self.create(file)

    def create_files_bulk(self, files_data: List[dict]) -> List[File]:
        """Create multiple file records efficiently."""
        # First, ensure all languages exist
        language_names = set(f.get("language_name") for f in files_data if f.get("language_name"))
        language_map = {}
        for name in language_names:
            language = self.get_or_create_language(name)
            language_map[name] = language.id

        # Create file records
        files = []
        for data in files_data:
            language_id = language_map.get(data.get("language_name"))
            file = File(
                project_id=data["project_id"],
                path=data["path"],
                language_id=language_id,
                file_size=data.get("file_size"),
                lines_of_code=data.get("lines_of_code"),
                comment_lines=data.get("comment_lines"),
                blank_lines=data.get("blank_lines"),
                created_timestamp=data.get("created_timestamp"),
                last_modified=data.get("last_modified"),
                content_hash=data.get("content_hash"),
            )
            files.append(file)

        return self.create_many(files)

    def count_by_project(self, project_id: int) -> int:
        """Count files in a project."""
        stmt = select(func.count(File.id)).where(File.project_id == project_id)
        return self.db.scalar(stmt) or 0

    def get_earliest_file_date(self, project_id: int) -> Optional[datetime]:
        """Return earliest created_timestamp for a project's files as datetime."""
        ts = self.db.scalar(
            select(func.min(File.created_timestamp)).where(File.project_id == project_id)
        )
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(ts)
        except Exception:
            return None

    def delete_by_project(self, project_id: int) -> int:
        """Delete all files for a project."""
        from sqlalchemy import delete
        stmt = delete(File).where(File.project_id == project_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
