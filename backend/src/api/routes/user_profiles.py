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
)
from src.services.user_profile_service import UserProfileService
from src.repositories.user_repository import UserRepository
from src.api.exceptions import (
    UserProfileNotFoundError,
    UserNotFoundError,
)
from src.api.dependencies import get_current_user
from src.models.orm.user import User

from .experience import router as experience_router

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


@router.get("/user/{user_id}", response_model=UserProfileDetail)
async def get_user_profile_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific user profile using user ID.

    - Returns full profile details
    """
    service = UserProfileService(db)
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


@router.put("/user/{user_id}", response_model=UserProfileDetail)
async def update_user_profile_by_user_id(
    user_id: int,
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a user profile using user ID.

    - Returns updated profile details
    """
    service = UserProfileService(db)
    profile = service.update_profile_by_user_id(user_id, data)
    if not profile:
        raise UserProfileNotFoundError(user_id)
    return profile


@router.delete("/user/{user_id}", status_code=204)
async def delete_user_profile_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a user profile using user ID.
    """
    service = UserProfileService(db)
    success = service.delete_profile_by_user_id(user_id)
    if not success:
        raise UserProfileNotFoundError(user_id)
    return

@router.get("/me", response_model=UserProfileDetail)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the current authenticated user's profile.
    """
    service = UserProfileService(db)
    profile = service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise UserProfileNotFoundError(current_user.id)
    return profile

@router.put("/me", response_model=UserProfileDetail)
async def upsert_my_profile(
    data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create or update the current authenticated user's profile.
    """
    service = UserProfileService(db)
    return service.upsert_profile_by_user_id(current_user.id, data)