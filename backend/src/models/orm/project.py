"""Project ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.file import File
    from src.models.orm.contributor import Contributor
    from src.models.orm.complexity import Complexity
    from src.models.orm.skill import ProjectSkill, ProjectSkillSummary, ProjectSkillTimeline
    from src.models.orm.resume import ResumeItem
    from src.models.orm.framework import ProjectFramework
    from src.models.orm.library import ProjectLibrary
    from src.models.orm.tool import ProjectTool


class Project(Base):
    """Project model representing an analyzed project."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    root_path: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="local")
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    zip_uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    first_file_created: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    first_commit_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    project_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    files: Mapped[List["File"]] = relationship(
        "File", back_populates="project", cascade="all, delete-orphan"
    )
    contributors: Mapped[List["Contributor"]] = relationship(
        "Contributor", back_populates="project", cascade="all, delete-orphan"
    )
    complexities: Mapped[List["Complexity"]] = relationship(
        "Complexity", back_populates="project", cascade="all, delete-orphan"
    )
    skills: Mapped[List["ProjectSkill"]] = relationship(
        "ProjectSkill", back_populates="project", cascade="all, delete-orphan"
    )
    skill_summary: Mapped[Optional["ProjectSkillSummary"]] = relationship(
        "ProjectSkillSummary", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    skill_timeline: Mapped[List["ProjectSkillTimeline"]] = relationship(
        "ProjectSkillTimeline", back_populates="project", cascade="all, delete-orphan"
    )
    resume_items: Mapped[List["ResumeItem"]] = relationship(
        "ResumeItem", back_populates="project", cascade="all, delete-orphan"
    )
    frameworks: Mapped[List["ProjectFramework"]] = relationship(
        "ProjectFramework", back_populates="project", cascade="all, delete-orphan"
    )
    libraries: Mapped[List["ProjectLibrary"]] = relationship(
        "ProjectLibrary", back_populates="project", cascade="all, delete-orphan"
    )
    tools: Mapped[List["ProjectTool"]] = relationship(
        "ProjectTool", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"
