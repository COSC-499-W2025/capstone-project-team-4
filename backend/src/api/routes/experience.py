"""Experience API routes."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.user_profile import (
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
)
from src.services.user_profile_service import UserProfileService
from src.api.exceptions import ExperienceNotFoundError

router = APIRouter(prefix="/user-profiles/{user_id}/experiences", tags=["experiences"])


@router.get("", response_model=List[ExperienceResponse])
async def get_experiences(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all experiences for a specific user.
    """
    service = UserProfileService(db)
    experiences = service.get_experiences_by_user_id(user_id)
    return experiences


@router.post("", response_model=ExperienceResponse, status_code=201)
async def create_experience(
    user_id: int,
    data: ExperienceCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new experience for a specific user.
    """
    service = UserProfileService(db)
    experience = service.create_experience(user_id, data)
    return experience


@router.put("/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    user_id: int,
    experience_id: int,
    data: ExperienceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing experience for a specific user.
    """
    service = UserProfileService(db)
    experience = service.update_experience(user_id, experience_id, data)
    if not experience:
        raise ExperienceNotFoundError(experience_id)
    return experience


@router.delete("/{experience_id}", status_code=204)
async def delete_experience(
    user_id: int,
    experience_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an experience for a specific user.
    """
    service = UserProfileService(db)
    success = service.delete_experience(user_id, experience_id)
    if not success:
        raise ExperienceNotFoundError(experience_id)
    return
