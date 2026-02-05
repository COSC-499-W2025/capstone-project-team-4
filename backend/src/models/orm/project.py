"""Project ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.file import File
    from src.models.orm.contributor import Contributor
    from src.models.orm.complexity import Complexity
    from src.models.orm.skill import ProjectSkill, ProjectSkillTimeline
    from src.models.orm.resume import ResumeItem
    from src.models.orm.framework import ProjectFramework
    from src.models.orm.library import ProjectLibrary
    from src.models.orm.tool import ProjectTool
    from src.models.orm.user import User
    from src.models.orm.snapshot import Snapshot


class Project(Base):
    """Project model representing an analyzed project."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
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

    # Snapshot reference (if this project represents a snapshot)
    snapshot_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("snapshots.id", ondelete="SET NULL", use_alter=True, name="fk_project_snapshot"),
        nullable=True,
        index=True,
        comment="If set, this project represents analysis data for a snapshot"
    )

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
    analysis_summary: Mapped[Optional["ProjectAnalysisSummary"]] = relationship(
        "ProjectAnalysisSummary", back_populates="project", uselist=False, cascade="all, delete-orphan"
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
    user: Mapped[Optional["User"]] = relationship("User", back_populates="projects")

    # Snapshot relationships
    snapshots: Mapped[List["Snapshot"]] = relationship(
        "Snapshot",
        foreign_keys="Snapshot.source_project_id",
        back_populates="source_project",
        cascade="all, delete-orphan",
        doc="Snapshots created from this project (if this is a source project)"
    )

    snapshot: Mapped[Optional["Snapshot"]] = relationship(
        "Snapshot",
        foreign_keys=[snapshot_id],
        back_populates="analyzed_project",
        doc="The snapshot this project represents (if this is snapshot analysis data)"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class ProjectAnalysisSummary(Base):
    """ProjectAnalysisSummary model for project analysis statistics and timing."""

    __tablename__ = "project_analysis_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    total_files_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_files_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    total_files_skipped: Mapped[int] = mapped_column(Integer, default=0)
    analysis_duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    # JSON-serialized mapping of stage -> duration (seconds) to spot slow phases
    analysis_stage_durations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="analysis_summary")

    def __repr__(self) -> str:
        return f"<ProjectAnalysisSummary(project_id={self.project_id}, duration={self.analysis_duration_seconds})>"
