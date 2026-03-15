"""Pydantic schemas for user authentication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user (registration)."""

    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response (excludes password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )


class UserLogin(BaseModel):
    """Schema for user login request."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema for login response."""

    access_token: str
    token_type: str
    message: str
    user: UserResponse
