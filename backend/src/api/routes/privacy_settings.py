"""Privacy settings API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.data_privacy_settings import (
    DataPrivacySettingsResponse,
    DataPrivacySettingsUpdate,
)
from src.repositories.data_privacy_settings_repository import (
    DataPrivacySettingsRepository,
)
from src.repositories.user_repository import UserRepository
from src.api.exceptions import UserNotFoundError, PrivacySettingsNotFoundError
from src.models.orm.user import User
from src.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/privacy-settings", tags=["privacy-settings"])


@router.get("/{user_id}", response_model=DataPrivacySettingsResponse)
async def get_privacy_settings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get privacy settings for a user.

    - Returns the user's AI consent settings
    - Creates default settings if none exist
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    user_repo = UserRepository(db)
    privacy_repo = DataPrivacySettingsRepository(db)

    # Verify user exists
    user = user_repo.get(user_id)
    if not user:
        raise UserNotFoundError(user_id)

    # Get or create privacy settings
    settings = privacy_repo.get_or_create_settings(user_id)

    return DataPrivacySettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        allow_ai_analysis=settings.allow_ai_analysis,
        allow_ai_resume_generation=settings.allow_ai_resume_generation,
        allow_data_collection=settings.allow_data_collection,
        consent_given_at=settings.consent_given_at,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.put("/{user_id}", response_model=DataPrivacySettingsResponse)
async def update_privacy_settings(
    user_id: int,
    data: DataPrivacySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update privacy settings for a user.

    - Updates AI consent preferences
    - Only provided fields will be updated
    - Automatically updates consent_given_at when consent is newly given
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    user_repo = UserRepository(db)
    privacy_repo = DataPrivacySettingsRepository(db)

    # Verify user exists
    user = user_repo.get(user_id)
    if not user:
        raise UserNotFoundError(user_id)

    # Get existing settings or create default ones
    existing_settings = privacy_repo.get_by_user_id(user_id)
    if not existing_settings:
        # Create default settings first
        privacy_repo.create_settings(user_id)

    # Update settings
    settings = privacy_repo.update_settings(
        user_id=user_id,
        allow_ai_analysis=data.allow_ai_analysis,
        allow_ai_resume_generation=data.allow_ai_resume_generation,
        allow_data_collection=data.allow_data_collection,
    )

    if not settings:
        raise PrivacySettingsNotFoundError(user_id)

    return DataPrivacySettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        allow_ai_analysis=settings.allow_ai_analysis,
        allow_ai_resume_generation=settings.allow_ai_resume_generation,
        allow_data_collection=settings.allow_data_collection,
        consent_given_at=settings.consent_given_at,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )
