"""Data privacy settings repository for database operations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.orm.data_privacy_settings import DataPrivacySettings
from src.repositories.base import BaseRepository


class DataPrivacySettingsRepository(BaseRepository[DataPrivacySettings]):
    """Repository for data privacy settings operations."""

    def __init__(self, db: Session):
        """Initialize data privacy settings repository."""
        super().__init__(DataPrivacySettings, db)

    def get_by_user_id(self, user_id: int) -> Optional[DataPrivacySettings]:
        """Get data privacy settings by user ID."""
        stmt = select(DataPrivacySettings).where(DataPrivacySettings.user_id == user_id)
        return self.db.scalar(stmt)

    def create_settings(
        self,
        user_id: int,
        allow_ai_analysis: bool = False,
        allow_ai_resume_generation: bool = False,
        allow_data_collection: bool = False,
    ) -> DataPrivacySettings:
        """
        Create data privacy settings for a user.

        Args:
            user_id: The ID of the user.
            allow_ai_analysis: Allow AI to analyze user data.
            allow_ai_resume_generation: Allow AI to generate resumes.
            allow_data_collection: Allow data collection for analytics.

        Returns:
            The created data privacy settings.
        """
        # Determine consent_given_at based on whether any consent was given
        consent_given_at = None
        if allow_ai_analysis or allow_ai_resume_generation or allow_data_collection:
            consent_given_at = datetime.utcnow()

        settings = DataPrivacySettings(
            user_id=user_id,
            allow_ai_analysis=allow_ai_analysis,
            allow_ai_resume_generation=allow_ai_resume_generation,
            allow_data_collection=allow_data_collection,
            consent_given_at=consent_given_at,
        )
        return self.create(settings)

    def update_settings(
        self,
        user_id: int,
        allow_ai_analysis: Optional[bool] = None,
        allow_ai_resume_generation: Optional[bool] = None,
        allow_data_collection: Optional[bool] = None,
    ) -> Optional[DataPrivacySettings]:
        """
        Update data privacy settings for a user.

        Args:
            user_id: The ID of the user.
            allow_ai_analysis: Allow AI to analyze user data.
            allow_ai_resume_generation: Allow AI to generate resumes.
            allow_data_collection: Allow data collection for analytics.

        Returns:
            The updated data privacy settings, or None if not found.
        """
        settings = self.get_by_user_id(user_id)
        if not settings:
            return None

        # Track if any new consent was given
        consent_newly_given = False

        if allow_ai_analysis is not None:
            if allow_ai_analysis and not settings.allow_ai_analysis:
                consent_newly_given = True
            settings.allow_ai_analysis = allow_ai_analysis

        if allow_ai_resume_generation is not None:
            if allow_ai_resume_generation and not settings.allow_ai_resume_generation:
                consent_newly_given = True
            settings.allow_ai_resume_generation = allow_ai_resume_generation

        if allow_data_collection is not None:
            if allow_data_collection and not settings.allow_data_collection:
                consent_newly_given = True
            settings.allow_data_collection = allow_data_collection

        # Update consent timestamp if new consent was given
        if consent_newly_given:
            settings.consent_given_at = datetime.utcnow()

        return self.update(settings)

    def get_or_create_settings(self, user_id: int) -> DataPrivacySettings:
        """
        Get existing settings or create default settings for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            The data privacy settings (existing or newly created).
        """
        settings = self.get_by_user_id(user_id)
        if settings:
            return settings
        return self.create_settings(user_id)
