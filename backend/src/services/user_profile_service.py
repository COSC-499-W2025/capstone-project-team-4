"""User profile service for user profile and work experience operations."""

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
    WorkExperienceCreate,
    WorkExperienceUpdate,
    WorkExperienceResponse,
)
from src.repositories.user_profile_repository import (
    UserProfileRepository,
    WorkExperienceRepository,
)

logger = logging.getLogger(__name__)


class UserProfileService:
    """Service for user profile and work experience operations."""

    def __init__(self, db: Session):
        """Initialize user profile service with database session."""
        self.db = db
        self.profile_repo = UserProfileRepository(db)
        self.experience_repo = WorkExperienceRepository(db)

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
                first_name=p.first_name,
                last_name=p.last_name,
                email=p.email,
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
        Get detailed user profile information with work experiences.

        Args:
            profile_id: ID of the user profile

        Returns:
            UserProfileDetail or None if not found
        """
        profile = self.profile_repo.get_with_work_experiences(profile_id)
        if not profile:
            return None

        work_experiences = [
            self._convert_work_experience(exp)
            for exp in profile.work_experiences
        ]

        return UserProfileDetail(
            id=profile.id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            email=profile.email,
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
            work_experiences=work_experiences,
        )

    def get_profile_by_email(self, email: str) -> Optional[UserProfileDetail]:
        """
        Get user profile by email.

        Args:
            email: Email of the user

        Returns:
            UserProfileDetail or None if not found
        """
        profile = self.profile_repo.get_by_email(email)
        if not profile:
            return None
        return self.get_profile(profile.id)

    def create_profile(self, data: UserProfileCreate) -> UserProfileDetail:
        """
        Create a new user profile with optional work experiences.

        Args:
            data: User profile creation data

        Returns:
            Created UserProfileDetail
        """
        profile = self.profile_repo.create_profile(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            city=data.city,
            state=data.state,
            country=data.country,
            linkedin_url=data.linkedin_url,
            github_url=data.github_url,
            portfolio_url=data.portfolio_url,
            summary=data.summary,
        )

        # Create work experiences if provided
        if data.work_experiences:
            for exp_data in data.work_experiences:
                self.experience_repo.create_work_experience(
                    user_profile_id=profile.id,
                    company_name=exp_data.company_name,
                    job_title=exp_data.job_title,
                    employment_type=exp_data.employment_type,
                    location=exp_data.location,
                    is_remote=exp_data.is_remote,
                    start_date=exp_data.start_date,
                    end_date=exp_data.end_date,
                    is_current=exp_data.is_current,
                    description=exp_data.description,
                    responsibilities=exp_data.responsibilities,
                    achievements=exp_data.achievements,
                )

        logger.info(f"Created user profile {profile.id}: {profile.email}")
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
        Delete a user profile and all associated work experiences.

        Args:
            profile_id: ID of the profile to delete

        Returns:
            True if deleted, False if not found
        """
        profile = self.profile_repo.get(profile_id)
        if not profile:
            return False

        logger.info(f"Deleting user profile {profile_id}: {profile.email}")
        return self.profile_repo.delete(profile_id)

    # Work Experience Operations
    def get_work_experiences(self, profile_id: int) -> List[WorkExperienceResponse]:
        """
        Get all work experiences for a user profile.

        Args:
            profile_id: ID of the user profile

        Returns:
            List of WorkExperienceResponse
        """
        experiences = self.experience_repo.get_by_user_profile(profile_id)
        return [self._convert_work_experience(exp) for exp in experiences]

    def create_work_experience(
        self,
        profile_id: int,
        data: WorkExperienceCreate,
    ) -> Optional[WorkExperienceResponse]:
        """
        Create a new work experience for a user profile.

        Args:
            profile_id: ID of the user profile
            data: Work experience creation data

        Returns:
            Created WorkExperienceResponse or None if profile not found
        """
        profile = self.profile_repo.get(profile_id)
        if not profile:
            return None

        experience = self.experience_repo.create_work_experience(
            user_profile_id=profile_id,
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

        logger.info(f"Created work experience {experience.id} for profile {profile_id}")
        return self._convert_work_experience(experience)

    def update_work_experience(
        self,
        experience_id: int,
        data: WorkExperienceUpdate,
    ) -> Optional[WorkExperienceResponse]:
        """
        Update an existing work experience.

        Args:
            experience_id: ID of the work experience to update
            data: Update data

        Returns:
            Updated WorkExperienceResponse or None if not found
        """
        update_data = data.model_dump(exclude_unset=True)
        experience = self.experience_repo.update_work_experience(
            experience_id,
            **update_data,
        )
        if not experience:
            return None

        logger.info(f"Updated work experience {experience_id}")
        return self._convert_work_experience(experience)

    def delete_work_experience(self, experience_id: int) -> bool:
        """
        Delete a work experience.

        Args:
            experience_id: ID of the work experience to delete

        Returns:
            True if deleted, False if not found
        """
        experience = self.experience_repo.get(experience_id)
        if not experience:
            return False

        logger.info(f"Deleting work experience {experience_id}")
        return self.experience_repo.delete(experience_id)

    def _convert_work_experience(self, exp) -> WorkExperienceResponse:
        """Convert ORM work experience to response schema."""
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

        return WorkExperienceResponse(
            id=exp.id,
            user_profile_id=exp.user_profile_id,
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
