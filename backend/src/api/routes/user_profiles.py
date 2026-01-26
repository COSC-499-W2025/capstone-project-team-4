"""User profiles API routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.user_profile import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileDetail,
    UserProfileList,
    WorkExperienceCreate,
    WorkExperienceUpdate,
    WorkExperienceResponse,
)
from src.services.user_profile_service import UserProfileService
from src.api.exceptions import (
    UserProfileNotFoundError,
    UserProfileEmailExistsError,
    WorkExperienceNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-profiles", tags=["user-profiles"])


# User Profile Endpoints
@router.get("", response_model=UserProfileList)
async def list_user_profiles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List all user profiles with pagination.

    - Returns a paginated list of user profile summaries
    - Includes basic personal information
    """
    service = UserProfileService(db)
    return service.list_profiles(page=page, page_size=page_size)


@router.get("/{profile_id}", response_model=UserProfileDetail)
async def get_user_profile(
    profile_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific user profile.

    - Returns full profile details including work experiences
    """
    service = UserProfileService(db)
    profile = service.get_profile(profile_id)

    if not profile:
        raise UserProfileNotFoundError(profile_id)

    return profile


@router.post("", response_model=UserProfileDetail, status_code=201)
async def create_user_profile(
    data: UserProfileCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user profile.

    - Creates a new user profile with personal information
    - Optionally includes work experiences
    - Email must be unique
    """
    service = UserProfileService(db)

    # Check if email already exists
    existing = service.get_profile_by_email(data.email)
    if existing:
        raise UserProfileEmailExistsError(data.email)

    return service.create_profile(data)


@router.put("/{profile_id}", response_model=UserProfileDetail)
async def update_user_profile(
    profile_id: int,
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing user profile.

    - Updates personal information fields
    - Only provided fields will be updated
    """
    service = UserProfileService(db)

    # Check if email is being changed and if new email already exists
    if data.email:
        existing = service.get_profile_by_email(data.email)
        if existing and existing.id != profile_id:
            raise UserProfileEmailExistsError(data.email)

    profile = service.update_profile(profile_id, data)

    if not profile:
        raise UserProfileNotFoundError(profile_id)

    return profile


@router.delete("/{profile_id}", status_code=204)
async def delete_user_profile(
    profile_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a user profile and all associated work experiences.

    - Permanently deletes the profile and all work experiences
    - This action cannot be undone
    """
    service = UserProfileService(db)
    deleted = service.delete_profile(profile_id)

    if not deleted:
        raise UserProfileNotFoundError(profile_id)


# Work Experience Endpoints
@router.get("/{profile_id}/work-experiences", response_model=List[WorkExperienceResponse])
async def get_work_experiences(
    profile_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all work experiences for a user profile.

    - Returns list of work experiences ordered by start date (most recent first)
    """
    service = UserProfileService(db)

    # Verify profile exists
    profile = service.get_profile(profile_id)
    if not profile:
        raise UserProfileNotFoundError(profile_id)

    return service.get_work_experiences(profile_id)


@router.post("/{profile_id}/work-experiences", response_model=WorkExperienceResponse, status_code=201)
async def create_work_experience(
    profile_id: int,
    data: WorkExperienceCreate,
    db: Session = Depends(get_db),
):
    """
    Add a new work experience to a user profile.

    - Creates a new work experience entry
    - Associates it with the specified user profile
    """
    service = UserProfileService(db)

    experience = service.create_work_experience(profile_id, data)

    if not experience:
        raise UserProfileNotFoundError(profile_id)

    return experience


@router.put("/{profile_id}/work-experiences/{experience_id}", response_model=WorkExperienceResponse)
async def update_work_experience(
    profile_id: int,
    experience_id: int,
    data: WorkExperienceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing work experience.

    - Updates work experience fields
    - Only provided fields will be updated
    """
    service = UserProfileService(db)

    # Verify profile exists
    profile = service.get_profile(profile_id)
    if not profile:
        raise UserProfileNotFoundError(profile_id)

    experience = service.update_work_experience(experience_id, data)

    if not experience:
        raise WorkExperienceNotFoundError(experience_id)

    return experience


@router.delete("/{profile_id}/work-experiences/{experience_id}", status_code=204)
async def delete_work_experience(
    profile_id: int,
    experience_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a work experience.

    - Permanently deletes the work experience entry
    - This action cannot be undone
    """
    service = UserProfileService(db)

    # Verify profile exists
    profile = service.get_profile(profile_id)
    if not profile:
        raise UserProfileNotFoundError(profile_id)

    deleted = service.delete_work_experience(experience_id)

    if not deleted:
        raise WorkExperienceNotFoundError(experience_id)
