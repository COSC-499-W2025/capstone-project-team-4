"""User profile and experience repository for database operations."""

import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.orm.user_profile import UserProfile
from src.models.orm.experience import Experience, ExperienceType
from src.repositories.base import BaseRepository


class UserProfileRepository(BaseRepository[UserProfile]):
    """Repository for user profile operations."""

    def __init__(self, db: Session):
        """Initialize user profile repository."""
        super().__init__(UserProfile, db)

    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile by user ID."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        return self.db.scalar(stmt)

    def create_profile(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
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
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
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


class ExperienceRepository(BaseRepository[Experience]):
    """Repository for experience operations."""

    def __init__(self, db: Session):
        """Initialize experience repository."""
        super().__init__(Experience, db)

    def get_by_user(self, user_id: int) -> List[Experience]:
        """Get all experiences for a user."""
        stmt = (
            select(Experience)
            .where(Experience.user_id == user_id)
            .order_by(Experience.start_date.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_user_and_type(
        self, user_id: int, experience_type: ExperienceType
    ) -> List[Experience]:
        """Get all experiences of a specific type for a user."""
        stmt = (
            select(Experience)
            .where(
                Experience.user_id == user_id,
                Experience.experience_type == experience_type.value,
            )
            .order_by(Experience.start_date.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create_experience(
        self,
        user_id: int,
        company_name: str,
        job_title: str,
        start_date,
        experience_type: str = ExperienceType.WORK.value,
        employment_type: Optional[str] = None,
        location: Optional[str] = None,
        is_remote: bool = False,
        end_date=None,
        is_current: bool = False,
        description: Optional[str] = None,
        responsibilities: Optional[List[str]] = None,
        achievements: Optional[List[str]] = None,
    ) -> Experience:
        """Create a new experience entry."""
        experience = Experience(
            user_id=user_id,
            experience_type=experience_type,
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

    def update_experience(
        self,
        experience_id: int,
        **kwargs,
    ) -> Optional[Experience]:
        """Update an existing experience entry."""
        experience = self.get(experience_id)
        if not experience:
            return None

        for key, value in kwargs.items():
            if hasattr(experience, key) and value is not None:
                if key in ("responsibilities", "achievements") and isinstance(value, list):
                    value = json.dumps(value)
                setattr(experience, key, value)

        return self.update(experience)

    def delete_by_user(self, user_id: int) -> int:
        """Delete all experiences for a user."""
        experiences = self.get_by_user(user_id)
        count = len(experiences)
        for exp in experiences:
            self.db.delete(exp)
        self.db.commit()
        return count
