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
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
)
from src.services.user_profile_service import UserProfileService
from src.repositories.user_repository import UserRepository
from src.api.exceptions import (
    UserProfileNotFoundError,
    UserNotFoundError,
    ExperienceNotFoundError,
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

    - Returns full profile details
    """
    service = UserProfileService(db)
    profile = service.get_profile(profile_id)

    if not profile:
        raise UserProfileNotFoundError(profile_id)

    return profile


@router.get("/user/{user_id}", response_model=UserProfileDetail)
async def get_user_profile_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get user profile by user ID.

    - Returns full profile details for a specific user
    """
    service = UserProfileService(db)
    user_repo = UserRepository(db)

    # Verify user exists
    user = user_repo.get(user_id)
    if not user:
        raise UserNotFoundError(user_id)

    profile = service.get_profile_by_user_id(user_id)

    if not profile:
        raise UserProfileNotFoundError(user_id)

    return profile


@router.post("/user/{user_id}", response_model=UserProfileDetail, status_code=201)
async def create_user_profile(
    user_id: int,
    data: UserProfileCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user profile for a user.

    - Creates a new user profile with personal information
    - User must exist
    """
    service = UserProfileService(db)
    user_repo = UserRepository(db)

    # Verify user exists
    user = user_repo.get(user_id)
    if not user:
        raise UserNotFoundError(user_id)

    return service.create_profile(user_id, data)


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
    Delete a user profile.

    - Permanently deletes the profile
    - This action cannot be undone
    """
    service = UserProfileService(db)
    deleted = service.delete_profile(profile_id)

    if not deleted:
        raise UserProfileNotFoundError(profile_id)


# Experience Endpoints
@router.get("/user/{user_id}/experiences", response_model=List[ExperienceResponse])
async def get_experiences(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all experiences for a user.

    - Returns list of experiences ordered by start date (most recent first)
    """
    service = UserProfileService(db)
    user_repo = UserRepository(db)

    # Verify user exists
    user = user_repo.get(user_id)
    if not user:
        raise UserNotFoundError(user_id)

    return service.get_experiences(user_id)


@router.post("/user/{user_id}/experiences", response_model=ExperienceResponse, status_code=201)
async def create_experience(
    user_id: int,
    data: ExperienceCreate,
    db: Session = Depends(get_db),
):
    """
    Add a new experience to a user.

    - Creates a new experience entry (work, education, volunteer, etc.)
    - Associates it with the specified user
    """
    service = UserProfileService(db)
    user_repo = UserRepository(db)

    # Verify user exists
    user = user_repo.get(user_id)
    if not user:
        raise UserNotFoundError(user_id)

    return service.create_experience(user_id, data)


@router.put("/experiences/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: int,
    data: ExperienceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing experience.

    - Updates experience fields
    - Only provided fields will be updated
    """
    service = UserProfileService(db)
    experience = service.update_experience(experience_id, data)

    if not experience:
        raise ExperienceNotFoundError(experience_id)

    return experience


@router.delete("/experiences/{experience_id}", status_code=204)
async def delete_experience(
    experience_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an experience.

    - Permanently deletes the experience entry
    - This action cannot be undone
    """
    service = UserProfileService(db)
    deleted = service.delete_experience(experience_id)

    if not deleted:
        raise ExperienceNotFoundError(experience_id)
