"""Full resume composition and export service."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.orm.experience import ExperienceType
from src.models.orm.project import Project
from src.models.schemas.full_resume import (
    FullResumeData,
    ResumeContactInfo,
    ResumeEducationItem,
    ResumeExperienceItem,
    ResumeProjectItem,
)
from src.repositories.education_repository import EducationRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.resume_repository import ResumeRepository
from src.repositories.skill_repository import SkillRepository
from src.repositories.user_profile_repository import ExperienceRepository, UserProfileRepository
from src.repositories.user_repository import UserRepository

# Path to the Jinja2 template
_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
_TEMPLATE_NAME = "resume_jake.html"


def _parse_json_field(value: Optional[str]) -> List[str]:
    """Parse a JSON-encoded list field, returning an empty list on failure."""
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
        return []
    except (json.JSONDecodeError, TypeError):
        return []


class FullResumeService:
    """Service for composing and exporting a full resume document."""

    def __init__(self, db: Session):
        self._db = db
        self._user_repo = UserRepository(db)
        self._profile_repo = UserProfileRepository(db)
        self._education_repo = EducationRepository(db)
        self._experience_repo = ExperienceRepository(db)
        self._project_repo = ProjectRepository(db)
        self._resume_repo = ResumeRepository(db)
        self._skill_repo = SkillRepository(db)

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def compose_resume(self, user_id: int) -> FullResumeData:
        """Aggregate all user data into a FullResumeData structure.

        Raises:
            ValueError: if the user does not exist.
        """
        user = self._user_repo.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        contact = self._build_contact(user)
        summary = self._get_summary(user_id)
        education = self._build_education(user_id)
        experience = self._build_experience(user_id)
        projects = self._build_projects(user_id)
        skills = self._aggregate_skills(user_id)

        return FullResumeData(
            contact=contact,
            summary=summary,
            education=education,
            experience=experience,
            projects=projects,
            skills=skills,
            generated_at=datetime.utcnow(),
        )

    def export_html(self, data: FullResumeData) -> str:
        """Render resume data to an HTML string using Jake's template."""
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template(_TEMPLATE_NAME)
        return template.render(
            contact=data.contact,
            summary=data.summary,
            education=data.education,
            experience=data.experience,
            projects=data.projects,
            skills=data.skills,
            generated_at=data.generated_at,
        )

    def export_pdf(self, data: FullResumeData) -> bytes:
        """Render resume data to a PDF byte string."""
        import weasyprint

        html_string = self.export_html(data)
        return weasyprint.HTML(string=html_string).write_pdf()

    def export_markdown(self, data: FullResumeData) -> str:
        """Render resume data to a Markdown string."""
        lines: List[str] = []

        # ── Header
        lines.append(f"# {data.contact.name}")
        contact_parts: List[str] = []
        if data.contact.email:
            contact_parts.append(data.contact.email)
        if data.contact.phone:
            contact_parts.append(data.contact.phone)
        if data.contact.linkedin_url:
            contact_parts.append(data.contact.linkedin_url)
        if data.contact.github_url:
            contact_parts.append(data.contact.github_url)
        if data.contact.portfolio_url:
            contact_parts.append(data.contact.portfolio_url)
        if data.contact.location:
            contact_parts.append(data.contact.location)
        if contact_parts:
            lines.append(" | ".join(contact_parts))
        lines.append("")

        # ── Summary
        if data.summary:
            lines.append("## Summary")
            lines.append(data.summary)
            lines.append("")

        # ── Education
        if data.education:
            lines.append("## Education")
            for edu in data.education:
                end_str = (
                    edu.end_date.strftime("%b %Y")
                    if edu.end_date and not edu.is_current
                    else "Present"
                )
                lines.append(
                    f"**{edu.institution}** — {edu.degree} in {edu.field_of_study}"
                )
                date_line = f"{edu.start_date.strftime('%b %Y')} – {end_str}"
                if edu.location:
                    date_line += f" | {edu.location}"
                lines.append(date_line)
                if edu.gpa is not None:
                    lines.append(f"GPA: {edu.gpa}")
                lines.append("")

        # ── Experience
        if data.experience:
            lines.append("## Experience")
            for exp in data.experience:
                end_str = (
                    exp.end_date.strftime("%b %Y")
                    if exp.end_date and not exp.is_current
                    else "Present"
                )
                remote_tag = " (Remote)" if exp.is_remote else ""
                lines.append(f"**{exp.company_name}** | {exp.job_title}{remote_tag}")
                date_line = f"{exp.start_date.strftime('%b %Y')} – {end_str}"
                if exp.location:
                    date_line += f" | {exp.location}"
                lines.append(date_line)
                bullets = list(exp.responsibilities or []) + list(exp.achievements or [])
                for b in bullets:
                    lines.append(f"- {b}")
                lines.append("")

        # ── Projects
        if data.projects:
            lines.append("## Projects")
            for proj in data.projects:
                tech_str = f" | {', '.join(proj.technologies)}" if proj.technologies else ""
                date_str = f" | {proj.date_label}" if proj.date_label else ""
                lines.append(f"**{proj.title}**{tech_str}{date_str}")
                for bullet in proj.highlights:
                    lines.append(f"- {bullet}")
                lines.append("")

        # ── Technical Skills
        if data.skills:
            lines.append("## Technical Skills")
            for category, skill_list in data.skills.items():
                lines.append(f"**{category}:** {', '.join(skill_list)}")
            lines.append("")

        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────

    def _build_contact(self, user) -> ResumeContactInfo:
        profile = self._profile_repo.get_by_user_id(user.id)
        if profile:
            name_parts = [profile.first_name, profile.last_name]
            name = " ".join(p for p in name_parts if p).strip() or "Your Name"
            location_parts = [profile.city, profile.state]
            location = ", ".join(p for p in location_parts if p) or None
            return ResumeContactInfo(
                name=name,
                email=user.email,
                phone=profile.phone,
                location=location,
                linkedin_url=profile.linkedin_url,
                github_url=profile.github_url,
                portfolio_url=profile.portfolio_url,
            )
        return ResumeContactInfo(name="Your Name", email=user.email)

    def _get_summary(self, user_id: int) -> Optional[str]:
        profile = self._profile_repo.get_by_user_id(user_id)
        return profile.summary if profile else None

    def _build_education(self, user_id: int) -> List[ResumeEducationItem]:
        records = self._education_repo.get_by_user(user_id)
        items = []
        for edu in records:
            items.append(
                ResumeEducationItem(
                    institution=edu.institution,
                    degree=edu.degree,
                    field_of_study=edu.field_of_study,
                    location=edu.location,
                    start_date=edu.start_date,
                    end_date=edu.end_date,
                    is_current=edu.is_current,
                    gpa=edu.gpa,
                )
            )
        return items

    def _build_experience(self, user_id: int) -> List[ResumeExperienceItem]:
        records = self._experience_repo.get_by_user_and_type(
            user_id, ExperienceType.WORK
        )
        items = []
        for exp in records:
            items.append(
                ResumeExperienceItem(
                    company_name=exp.company_name,
                    job_title=exp.job_title,
                    location=exp.location,
                    is_remote=exp.is_remote,
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    is_current=exp.is_current,
                    responsibilities=_parse_json_field(exp.responsibilities),
                    achievements=_parse_json_field(exp.achievements),
                )
            )
        return items

    def _build_projects(self, user_id: int) -> List[ResumeProjectItem]:
        stmt = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        projects = list(self._db.scalars(stmt).all())

        items = []
        for project in projects:
            resume_item = self._resume_repo.get_latest(project.id)
            highlights = resume_item.highlights or [] if resume_item else []

            technologies = self._get_top_skills(project.id, limit=6)

            date_label = None
            if project.project_started_at:
                date_label = project.project_started_at.strftime("%b %Y")
            elif project.created_at:
                date_label = project.created_at.strftime("%b %Y")

            items.append(
                ResumeProjectItem(
                    title=resume_item.title if resume_item else project.name,
                    technologies=technologies,
                    highlights=highlights,
                    date_label=date_label,
                )
            )
        return items

    def _get_top_skills(self, project_id: int, limit: int = 6) -> List[str]:
        """Flatten top skills across all categories for a project."""
        grouped = self._skill_repo.get_grouped_by_category(project_id)
        skills: List[str] = []
        for category_skills in grouped.values():
            for ps in category_skills:
                skills.append(ps.skill.name)
        return skills[:limit]

    def _aggregate_skills(self, user_id: int) -> Dict[str, List[str]]:
        """Merge skills across all user projects, grouped by category."""
        stmt = select(Project).where(Project.user_id == user_id)
        projects = list(self._db.scalars(stmt).all())

        aggregated: Dict[str, List[str]] = {}
        for project in projects:
            grouped = self._skill_repo.get_grouped_by_category(project.id)
            for category, project_skills in grouped.items():
                if category not in aggregated:
                    aggregated[category] = []
                for ps in project_skills:
                    name = ps.skill.name
                    if name not in aggregated[category]:
                        aggregated[category].append(name)

        # Sort skills alphabetically within each category
        return {
            cat: sorted(skills)
            for cat, skills in sorted(aggregated.items())
        }
