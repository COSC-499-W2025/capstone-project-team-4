"""Contributor ORM models."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project
    from src.models.orm.contributor_commit import ContributorCommit


class Contributor(Base):
    """Contributor model representing a git contributor."""

    __tablename__ = "contributors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    github_username: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    github_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    commits: Mapped[int] = mapped_column(Integer, default=0)
    percent: Mapped[float] = mapped_column(Float, default=0.0)
    total_lines_added: Mapped[int] = mapped_column(Integer, default=0)
    total_lines_deleted: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="contributors")
    files_modified: Mapped[List["ContributorFile"]] = relationship(
        "ContributorFile", back_populates="contributor", cascade="all, delete-orphan"
    )
    commit_history: Mapped[List["ContributorCommit"]] = relationship(
        "ContributorCommit", back_populates="contributor", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Contributor(id={self.id}, name='{self.name}')>"


class ContributorFile(Base):
    """ContributorFile model representing files modified by a contributor."""

    __tablename__ = "contributor_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    contributor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contributors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    modifications: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    contributor: Mapped["Contributor"] = relationship(
        "Contributor", back_populates="files_modified"
    )

    def __repr__(self) -> str:
        return f"<ContributorFile(id={self.id}, filename='{self.filename}')>"
