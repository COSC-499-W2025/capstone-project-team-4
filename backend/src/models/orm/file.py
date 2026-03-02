"""File ORM models."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, Column, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project


class Language(Base):
    """Language lookup table for normalization."""

    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # Relationships
    files: Mapped[List["File"]] = relationship("File", back_populates="language")

    def __repr__(self) -> str:
        return f"<Language(id={self.id}, name='{self.name}')>"


class File(Base):
    """File model representing a file in an analyzed project."""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)
    language_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("languages.id"), nullable=True, index=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lines_of_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment_lines: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blank_lines: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_timestamp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_modified: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    content_hash = Column(String(64), index=True, nullable=True) # SHA-256 hash of file content for deduplication
    #__table_args__ = (UniqueConstraint("project_id", "path", name="uq_files_project_path"),) # Unique constraint on content_hash for deduplication
    #Index("ix_files_project_id", "project_id")
    #Index("ix_files_content_hash", "content_hash")
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="files")
    language: Mapped[Optional["Language"]] = relationship("Language", back_populates="files")

    def __repr__(self) -> str:
        return f"<File(id={self.id}, path='{self.path}')>"
