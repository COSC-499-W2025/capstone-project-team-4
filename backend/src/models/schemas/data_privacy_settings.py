"""Pydantic schemas for data privacy settings."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DataPrivacySettingsBase(BaseModel):
    """Base data privacy settings schema."""

    allow_ai_analysis: bool = False
    allow_ai_resume_generation: bool = False
    allow_data_collection: bool = False


class DataPrivacySettingsCreate(DataPrivacySettingsBase):
    """Schema for creating data privacy settings."""

    pass


class DataPrivacySettingsUpdate(BaseModel):
    """Schema for updating data privacy settings."""

    allow_ai_analysis: Optional[bool] = None
    allow_ai_resume_generation: Optional[bool] = None
    allow_data_collection: Optional[bool] = None


class DataPrivacySettingsResponse(DataPrivacySettingsBase):
    """Schema for data privacy settings response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    consent_given_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
