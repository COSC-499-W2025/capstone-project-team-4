"""User profile repository for database operations."""

import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.models.orm.user_profile import UserProfile
from src.models.orm.work_experience import WorkExperience
from src.repositories.base import BaseRepository


class UserProfileRepository(BaseRepository[UserProfile]):
    """Repository for user profile operations."""

    def __init__(self, db: Session):
        """Initialize user profile repository."""
        super().__init__(UserProfile, db)

    def get_by_email(self, email: str) -> Optional[UserProfile]:
        """Get user profile by email."""
        stmt = select(UserProfile).where(UserProfile.email == email)
        return self.db.scalar(stmt)

    def get_with_work_experiences(self, user_profile_id: int) -> Optional[UserProfile]:
        """Get user profile with work experiences loaded."""
        stmt = (
            select(UserProfile)
            .options(joinedload(UserProfile.work_experiences))
            .where(UserProfile.id == user_profile_id)
        )
        return self.db.scalar(stmt)

    def create_profile(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        github_url: Optional[str] = None,
        portfolio_url: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> UserProfile:
        """Create a new user profile."""
        profile = UserProfile(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            city=city,
            state=state,
            country=country,
            linkedin_url=linkedin_url,
            github_url=github_url,
            portfolio_url=portfolio_url,
            summary=summary,
        )
        return self.create(profile)

    def update_profile(
        self,
        user_profile_id: int,
        **kwargs,
    ) -> Optional[UserProfile]:
        """Update an existing user profile."""
        profile = self.get(user_profile_id)
        if not profile:
            return None

        for key, value in kwargs.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)

        return self.update(profile)


class WorkExperienceRepository(BaseRepository[WorkExperience]):
    """Repository for work experience operations."""

    def __init__(self, db: Session):
        """Initialize work experience repository."""
        super().__init__(WorkExperience, db)

    def get_by_user_profile(self, user_profile_id: int) -> List[WorkExperience]:
        """Get all work experiences for a user profile."""
        stmt = (
            select(WorkExperience)
            .where(WorkExperience.user_profile_id == user_profile_id)
            .order_by(WorkExperience.start_date.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create_work_experience(
        self,
        user_profile_id: int,
        company_name: str,
        job_title: str,
        start_date,
        employment_type: Optional[str] = None,
        location: Optional[str] = None,
        is_remote: bool = False,
        end_date=None,
        is_current: bool = False,
        description: Optional[str] = None,
        responsibilities: Optional[List[str]] = None,
        achievements: Optional[List[str]] = None,
    ) -> WorkExperience:
        """Create a new work experience entry."""
        experience = WorkExperience(
            user_profile_id=user_profile_id,
            company_name=company_name,
            job_title=job_title,
            employment_type=employment_type,
            location=location,
            is_remote=is_remote,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description,
            responsibilities=json.dumps(responsibilities) if responsibilities else None,
            achievements=json.dumps(achievements) if achievements else None,
        )
        return self.create(experience)

    def update_work_experience(
        self,
        work_experience_id: int,
        **kwargs,
    ) -> Optional[WorkExperience]:
        """Update an existing work experience entry."""
        experience = self.get(work_experience_id)
        if not experience:
            return None

        for key, value in kwargs.items():
            if hasattr(experience, key) and value is not None:
                if key in ("responsibilities", "achievements") and isinstance(value, list):
                    value = json.dumps(value)
                setattr(experience, key, value)

        return self.update(experience)

    def delete_by_user_profile(self, user_profile_id: int) -> int:
        """Delete all work experiences for a user profile."""
        experiences = self.get_by_user_profile(user_profile_id)
        count = len(experiences)
        for exp in experiences:
            self.db.delete(exp)
        self.db.commit()
        return count
