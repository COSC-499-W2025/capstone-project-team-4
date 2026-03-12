"""Portfolio service for portfolio operations."""

import logging
from typing import Dict, List, Any, Tuple, Optional, Union

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.config.settings import settings
from src.models.orm.portfolio import Portfolio
from src.models.orm.user import User
from src.models.schemas.portfolio import (
    PortfolioResponse,
    PortfolioProjectCustomize,
    PortfolioUpdate,
)
from src.repositories.portfolio_repository import PortfolioRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.skill_repository import SkillRepository
from src.repositories.resume_repository import ResumeRepository
from src.repositories.user_profile_repository import (
    UserProfileRepository,
    ExperienceRepository,
)
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
        user_name = (
            f"{profile.first_name} {profile.last_name}" if profile else user.email
        )
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

            projects_data.append(
                {
                    "name": project.name,
                    "languages": languages,
                    "frameworks": frameworks,
                    "skills": skill_categories,
                    "resume_highlights": highlights or [],
                }
            )

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

    def get_portfolio(self, portfolio_id: int) -> Optional[PortfolioResponse]:
        """
        Get a portfolio by ID (public, no auth required).

        Args:
            portfolio_id: The portfolio ID to retrieve

        Returns:
            PortfolioResponse if found, None if not found
        """
        portfolio = self.portfolio_repo.get(portfolio_id)
        if portfolio is None:
            return None

        return PortfolioResponse(
            id=portfolio.id,
            user_id=portfolio.user_id,
            title=portfolio.title,
            summary=portfolio.summary,
            content=portfolio.content,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
        )

    def update_portfolio(
        self,
        portfolio_id: int,
        data: PortfolioUpdate,
        user: User,
    ) -> Optional[Union[PortfolioResponse, str]]:
        """
        Update a portfolio by ID.

        Args:
            portfolio_id: The portfolio ID to update
            data: PortfolioUpdate with fields to change (None fields are skipped)
            user: The authenticated User ORM object

        Returns:
            PortfolioResponse on success, None if not found, "forbidden" if not owned
        """
        portfolio = self.portfolio_repo.get(portfolio_id)
        if portfolio is None:
            return None

        if portfolio.user_id != user.id:
            return "forbidden"

        if data.title is not None:
            portfolio.title = data.title
        if data.summary is not None:
            portfolio.summary = data.summary
        if data.content is not None:
            portfolio.content = data.content

        portfolio = self.portfolio_repo.update(portfolio)

        logger.info(f"Updated portfolio {portfolio.id} for user {user.id}")

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
            result.append(
                {
                    "company_name": exp.company_name,
                    "job_title": exp.job_title,
                    "experience_type": exp.experience_type,
                    "start_date": str(exp.start_date) if exp.start_date else None,
                    "end_date": str(exp.end_date) if exp.end_date else None,
                    "is_current": exp.is_current,
                    "description": exp.description,
                }
            )
        return result

    def customize_project(
        self,
        portfolio_id: int,
        user_id: int,
        project_name: str,
        update_data: PortfolioProjectCustomize,
    ) -> Tuple[Optional[PortfolioResponse], Optional[str]]:
        """
        Updates custom fields for a specific project inside the portfolio JSON.
        """
        # Fetch portfolio
        portfolio = self.portfolio_repo.get(portfolio_id)
        if not portfolio:
            return None, "Portfolio not found"

        # Security Check
        if portfolio.user_id != user_id:
            return None, "Not authorized to edit this portfolio"

        #  Open that "content" thing filled with projects
        content = portfolio.content or {}
        projects = content.get("projects", [])

        # Find the project and edit it
        project_found = False
        for proj in projects:
            if proj.get("name") == project_name:
                project_found = True

                # Apply the customizations
                if update_data.name is not None:
                    proj["name"] = update_data.name
                if update_data.languages is not None:
                    proj["languages"] = update_data.languages
                if update_data.frameworks is not None:
                    proj["frameworks"] = update_data.frameworks
                if update_data.resume_highlights is not None:
                    proj["resume_highlights"] = update_data.resume_highlights
                # Custom stuff here
                if update_data.custom_name is not None:
                    proj["custom_name"] = update_data.custom_name
                if update_data.description is not None:
                    proj["description"] = update_data.description
                if update_data.live_demo_url is not None:
                    proj["live_demo_url"] = update_data.live_demo_url
                break

        if not project_found:
            return None, f"Project '{project_name}' not found in portfolio"

        # Save the JSON back and return
        portfolio.content = content
        flag_modified(portfolio, "content")

        updated_portfolio = self.portfolio_repo.update(portfolio)

        return PortfolioResponse(
            id=updated_portfolio.id,
            user_id=updated_portfolio.user_id,
            title=updated_portfolio.title,
            summary=updated_portfolio.summary,
            content=updated_portfolio.content,
            created_at=updated_portfolio.created_at,
            updated_at=updated_portfolio.updated_at,
        ), None
