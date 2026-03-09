"""User profile service for user profile and experience operations."""

import json
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.schemas.user_profile import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileSummary,
    UserProfileDetail,
    UserProfileList,
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
)
from src.repositories.user_profile_repository import (
    UserProfileRepository,
    ExperienceRepository,
)

logger = logging.getLogger(__name__)


class UserProfileService:
    """Service for user profile and experience operations."""

    def __init__(self, db: Session):
        """Initialize user profile service with database session."""
        self.db = db
        self.profile_repo = UserProfileRepository(db)
        self.experience_repo = ExperienceRepository(db)

    def list_profiles(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> UserProfileList:
        """
        List all user profiles with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            UserProfileList with paginated results
        """
        skip = (page - 1) * page_size
        total = self.profile_repo.count()
        pages = (total + page_size - 1) // page_size if total > 0 else 1

        profiles = self.profile_repo.get_all(skip=skip, limit=page_size)

        items = [
            UserProfileSummary(
                id=p.id,
                user_id=p.user_id,
                first_name=p.first_name,
                last_name=p.last_name,
                phone=p.phone,
                city=p.city,
                state=p.state,
                country=p.country,
                linkedin_url=p.linkedin_url,
                github_url=p.github_url,
                portfolio_url=p.portfolio_url,
                summary=p.summary,
                created_at=p.created_at,
            )
            for p in profiles
        ]

        return UserProfileList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_profile(self, profile_id: int) -> Optional[UserProfileDetail]:
        """
        Get detailed user profile information.

        Args:
            profile_id: ID of the user profile

        Returns:
            UserProfileDetail or None if not found
        """
        profile = self.profile_repo.get(profile_id)
        if not profile:
            return None

        return UserProfileDetail(
            id=profile.id,
            user_id=profile.user_id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            phone=profile.phone,
            city=profile.city,
            state=profile.state,
            country=profile.country,
            linkedin_url=profile.linkedin_url,
            github_url=profile.github_url,
            portfolio_url=profile.portfolio_url,
            summary=profile.summary,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def get_profile_by_user_id(self, user_id: int) -> Optional[UserProfileDetail]:
        """
        Get user profile by user ID.

        Args:
            user_id: ID of the user

        Returns:
            UserProfileDetail or None if not found
        """
        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return None
        return self.get_profile(profile.id)

    def create_profile(self, user_id: int, data: UserProfileCreate) -> UserProfileDetail:
        """
        Create a new user profile.

        Args:
            user_id: ID of the user
            data: User profile creation data

        Returns:
            Created UserProfileDetail
        """
        profile = self.profile_repo.create_profile(
            user_id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            city=data.city,
            state=data.state,
            country=data.country,
            linkedin_url=data.linkedin_url,
            github_url=data.github_url,
            portfolio_url=data.portfolio_url,
            summary=data.summary,
        )

        logger.info(f"Created user profile {profile.id} for user {user_id}")
        return self.get_profile(profile.id)

    def update_profile(
        self,
        profile_id: int,
        data: UserProfileUpdate,
    ) -> Optional[UserProfileDetail]:
        """
        Update an existing user profile.

        Args:
            profile_id: ID of the profile to update
            data: Update data

        Returns:
            Updated UserProfileDetail or None if not found
        """
        update_data = data.model_dump(exclude_unset=True)
        profile = self.profile_repo.update_profile(profile_id, **update_data)
        if not profile:
            return None

        logger.info(f"Updated user profile {profile_id}")
        return self.get_profile(profile_id)

    def delete_profile(self, profile_id: int) -> bool:
        """
        Delete a user profile.

        Args:
            profile_id: ID of the profile to delete

        Returns:
            True if deleted, False if not found
        """
        profile = self.profile_repo.get(profile_id)
        if not profile:
            return False

        logger.info(f"Deleting user profile {profile_id}")
        return self.profile_repo.delete(profile_id)

    # Experience Operations
    def get_experiences(self, user_id: int) -> List[ExperienceResponse]:
        """
        Get all experiences for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of ExperienceResponse
        """
        experiences = self.experience_repo.get_by_user(user_id)
        return [self._convert_experience(exp) for exp in experiences]

    def create_experience(
        self,
        user_id: int,
        data: ExperienceCreate,
    ) -> ExperienceResponse:
        """
        Create a new experience for a user.

        Args:
            user_id: ID of the user
            data: Experience creation data

        Returns:
            Created ExperienceResponse
        """
        experience = self.experience_repo.create_experience(
            user_id=user_id,
            experience_type=data.experience_type.value,
            company_name=data.company_name,
            job_title=data.job_title,
            employment_type=data.employment_type,
            location=data.location,
            is_remote=data.is_remote,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current,
            description=data.description,
            responsibilities=data.responsibilities,
            achievements=data.achievements,
        )

        logger.info(f"Created experience {experience.id} for user {user_id}")
        return self._convert_experience(experience)

    def update_experience(
        self,
        experience_id: int,
        data: ExperienceUpdate,
    ) -> Optional[ExperienceResponse]:
        """
        Update an existing experience.

        Args:
            experience_id: ID of the experience to update
            data: Update data

        Returns:
            Updated ExperienceResponse or None if not found
        """
        update_data = data.model_dump(exclude_unset=True)

        # Convert experience_type enum to string if present
        if "experience_type" in update_data and update_data["experience_type"] is not None:
            update_data["experience_type"] = update_data["experience_type"].value

        experience = self.experience_repo.update_experience(
            experience_id,
            **update_data,
        )
        if not experience:
            return None

        logger.info(f"Updated experience {experience_id}")
        return self._convert_experience(experience)

    def delete_experience(self, experience_id: int) -> bool:
        """
        Delete an experience.

        Args:
            experience_id: ID of the experience to delete

        Returns:
            True if deleted, False if not found
        """
        experience = self.experience_repo.get(experience_id)
        if not experience:
            return False

        logger.info(f"Deleting experience {experience_id}")
        return self.experience_repo.delete(experience_id)

    def _convert_experience(self, exp) -> ExperienceResponse:
        """Convert ORM experience to response schema."""
        responsibilities = None
        achievements = None

        if exp.responsibilities:
            try:
                responsibilities = json.loads(exp.responsibilities)
            except json.JSONDecodeError:
                responsibilities = None

        if exp.achievements:
            try:
                achievements = json.loads(exp.achievements)
            except json.JSONDecodeError:
                achievements = None

        return ExperienceResponse(
            id=exp.id,
            user_id=exp.user_id,
            experience_type=exp.experience_type,
            company_name=exp.company_name,
            job_title=exp.job_title,
            employment_type=exp.employment_type,
            location=exp.location,
            is_remote=exp.is_remote,
            start_date=exp.start_date,
            end_date=exp.end_date,
            is_current=exp.is_current,
            description=exp.description,
            responsibilities=responsibilities,
            achievements=achievements,
            created_at=exp.created_at,
            updated_at=exp.updated_at,
        )

    def upsert_profile_by_user_id(
        self,
        user_id: int,
        data: UserProfileCreate,
    ) -> UserProfileDetail:
        """
        Create or update a user profile by user ID.

        Args:
            user_id: ID of the user
            data: Full profile data

        Returns:
            UserProfileDetail
        """
        existing = self.profile_repo.get_by_user_id(user_id)

        if not existing:
            return self.create_profile(user_id, data)

        update_data = data.model_dump()
        profile = self.profile_repo.update_profile(existing.id, **update_data)

        logger.info(f"Upserted user profile for user {user_id}")
        return self.get_profile(profile.id)