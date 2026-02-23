"""Portfolio service for portfolio operations."""

import logging
from typing import Dict, List, Any

from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.orm.portfolio import Portfolio
from src.models.orm.user import User
from src.models.schemas.portfolio import PortfolioResponse
from src.repositories.portfolio_repository import PortfolioRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.skill_repository import SkillRepository
from src.repositories.resume_repository import ResumeRepository
from src.repositories.user_profile_repository import UserProfileRepository, ExperienceRepository
from src.core.generators.portfolio import generate_portfolio

logger = logging.getLogger(__name__)


class PortfolioService:
    """Service for portfolio operations."""

    def __init__(self, db: Session):
        """Initialize portfolio service with database session."""
        self.db = db
        self.portfolio_repo = PortfolioRepository(db)
        self.project_repo = ProjectRepository(db)
        self.skill_repo = SkillRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.profile_repo = UserProfileRepository(db)
        self.experience_repo = ExperienceRepository(db)

    def generate_portfolio(self, user: User) -> PortfolioResponse:
        """
        Generate or regenerate a portfolio for the authenticated user.

        Aggregates all project data, skills, resume items, profile, and experiences.
        Uses AI to generate a summary, with template fallback.
        Upserts the result into the portfolios table.

        Args:
            user: The authenticated User ORM object

        Returns:
            PortfolioResponse with generated portfolio data
        """
        user_id = user.id

        # 1. Get user profile for name and summary
        profile = self.profile_repo.get_by_user_id(user_id)
        user_name = f"{profile.first_name} {profile.last_name}" if profile else user.email
        profile_summary = profile.summary if profile else None

        # 2. Get all user's projects
        projects = self.project_repo.get_by_user_id(user_id)

        # 3. For each project, gather languages, frameworks, skills, resume highlights
        projects_data = []
        aggregated_skills: Dict[str, List[str]] = {}

        for project in projects:
            project_id = project.id
            languages = self.project_repo.get_languages(project_id)
            frameworks = self.project_repo.get_frameworks(project_id)

            # Skills grouped by category
            skill_categories = self._get_skill_categories(project_id)
            for cat, skills in skill_categories.items():
                if cat not in aggregated_skills:
                    aggregated_skills[cat] = []
                aggregated_skills[cat].extend(skills)

            # Latest resume highlights
            latest_resume = self.resume_repo.get_latest(project_id)
            highlights = latest_resume.highlights if latest_resume else []

            projects_data.append({
                "name": project.name,
                "languages": languages,
                "frameworks": frameworks,
                "skills": skill_categories,
                "resume_highlights": highlights or [],
            })

        # Deduplicate aggregated skills
        for cat in aggregated_skills:
            aggregated_skills[cat] = sorted(set(aggregated_skills[cat]))

        # 4. Get user experiences
        experiences_data = self._get_experiences_data(user_id)

        # 5. Generate portfolio via AI/template
        generated = generate_portfolio(
            user_name=user_name,
            projects_data=projects_data,
            aggregated_skills=aggregated_skills,
            experiences=experiences_data,
            profile_summary=profile_summary,
            use_ai=settings.ai_resume_generation,
            api_key=settings.openai_api_key,
            ai_model=settings.ai_model,
            ai_temperature=settings.ai_temperature,
            ai_max_tokens=settings.ai_max_tokens,
        )

        # 6. Build content JSON
        content = {
            "projects": projects_data,
            "aggregated_skills": aggregated_skills,
            "experiences": experiences_data,
        }

        # 7. Upsert portfolio
        existing = self.portfolio_repo.get_by_user_id(user_id)
        if existing:
            existing.title = generated.get("title", "My Portfolio")
            existing.summary = generated.get("summary", "")
            existing.content = content
            portfolio = self.portfolio_repo.update(existing)
        else:
            portfolio = Portfolio(
                user_id=user_id,
                title=generated.get("title", "My Portfolio"),
                summary=generated.get("summary", ""),
                content=content,
            )
            portfolio = self.portfolio_repo.create(portfolio)

        logger.info(f"Generated portfolio {portfolio.id} for user {user_id}")

        return PortfolioResponse(
            id=portfolio.id,
            user_id=portfolio.user_id,
            title=portfolio.title,
            summary=portfolio.summary,
            content=portfolio.content,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
        )

    def _get_skill_categories(self, project_id: int) -> Dict[str, List[str]]:
        """Get skill categories for a project as string lists."""
        skills_grouped = self.skill_repo.get_grouped_by_category(project_id)
        result = {}
        for category, project_skills in skills_grouped.items():
            result[category] = [ps.skill.name for ps in project_skills]
        return result

    def _get_experiences_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Get experiences formatted for portfolio generation."""
        experiences = self.experience_repo.get_by_user(user_id)
        result = []
        for exp in experiences:
            result.append({
                "company_name": exp.company_name,
                "job_title": exp.job_title,
                "experience_type": exp.experience_type,
                "start_date": str(exp.start_date) if exp.start_date else None,
                "end_date": str(exp.end_date) if exp.end_date else None,
                "is_current": exp.is_current,
                "description": exp.description,
            })
        return result
