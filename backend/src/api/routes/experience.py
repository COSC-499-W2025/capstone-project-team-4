"""Experience API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.user_profile import (
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
)
from src.services.user_profile_service import UserProfileService
from src.api.exceptions import ExperienceNotFoundError

from src.models.orm.user import User
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/user-profiles/{user_id}/experiences", tags=["experiences"])


@router.get("", response_model=List[ExperienceResponse])
async def get_experiences(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all experiences for a specific user.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    service = UserProfileService(db)
    experiences = service.get_experiences(user_id)
    return experiences


@router.post("", response_model=ExperienceResponse, status_code=201)
async def create_experience(
    user_id: int,
    data: ExperienceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new experience for a specific user.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    service = UserProfileService(db)
    experience = service.create_experience(user_id, data)
    return experience


@router.put("/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    user_id: int,
    experience_id: int,
    data: ExperienceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing experience for a specific user.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    service = UserProfileService(db)
    experience = service.update_experience(experience_id, data)
    if not experience:
        raise ExperienceNotFoundError(experience_id)
    return experience


@router.delete("/{experience_id}", status_code=204)
async def delete_experience(
    user_id: int,
    experience_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an experience for a specific user.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    service = UserProfileService(db)
    success = service.delete_experience(experience_id)
    if not success:
        raise ExperienceNotFoundError(experience_id)
    return
