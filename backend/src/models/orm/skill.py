"""Skill ORM models."""

from datetime import date as date_type
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.project import Project


class Skill(Base):
    """Skill lookup table for normalization."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Relationships
    project_skills: Mapped[list["ProjectSkill"]] = relationship(
        "ProjectSkill", back_populates="skill", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("name", "category", name="uq_skill_name_category"),
    )

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}', category='{self.category}')>"


class ProjectSkill(Base):
    """ProjectSkill model representing skills detected in a project."""

    __tablename__ = "project_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frequency: Mapped[int] = mapped_column(Integer, default=1)

    # Source tracking for complementary detection system
    # Values: "language", "framework", "library", "tool", "contextual", "file_type"
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="project_skills")

    __table_args__ = (
        UniqueConstraint("project_id", "skill_id", name="uq_project_skill"),
    )

    def __repr__(self) -> str:
        return f"<ProjectSkill(id={self.id}, project_id={self.project_id}, skill_id={self.skill_id}, source='{self.source}')>"


class ProjectSkillTimeline(Base):
    """ProjectSkillTimeline model for skill heatmap/timeline."""

    __tablename__ = "project_skill_timelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="skill_timeline")

    __table_args__ = (
        UniqueConstraint("project_id", "skill", "date", name="uq_project_skill_date"),
    )

    def __repr__(self) -> str:
        return f"<ProjectSkillTimeline(project_id={self.project_id}, skill='{self.skill}')>"
