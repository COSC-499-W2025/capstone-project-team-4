"""Authentication service for user registration and login."""

import logging
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from src.core.security import verify_password, create_access_token
from src.models.orm.user import User
from src.models.schemas.user import UserCreate, UserResponse, UserLogin, LoginResponse
from src.repositories.user_repository import UserRepository
from src.repositories.data_privacy_settings_repository import (
    DataPrivacySettingsRepository,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        """Initialize auth service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)
        self.privacy_repo = DataPrivacySettingsRepository(db)

    def register(
        self, data: UserCreate
    ) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Register a new user.

        Args:
            data: User registration data.

        Returns:
            Tuple of (UserResponse, None) on success,
            or (None, error_message) on failure.
        """
        # Check if email already exists
        if self.user_repo.email_exists(data.email):
            return None, "Email already registered"

        # Create user
        user = self.user_repo.create_user(
            email=data.email,
            password=data.password,
        )

        # Create default privacy settings for the user
        self.privacy_repo.create_settings(user_id=user.id)

        logger.info(f"Registered new user: {user.email}")

        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ), None

    def authenticate(
        self, data: UserLogin
    ) -> Tuple[Optional[LoginResponse], Optional[str]]:
        """
        Authenticate a user with email and password.

        Args:
            data: User login credentials.

        Returns:
            Tuple of (LoginResponse, None) on success,
            or (None, error_message) on failure.
        """
        # Get user by email
        user = self.user_repo.get_by_email(data.email)

        if not user:
            return None, "Invalid email or password"

        # Check if account is active
        if not user.is_active:
            return None, "Account is deactivated"

        # Verify password
        if not verify_password(data.password, user.password_hash):
            return None, "Invalid email or password"

        logger.info(f"User authenticated: {user.email}")

        # Generate token
        access_token = create_access_token(subject=user.id)

        user_response = UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        # Idk wtf this loginresponse is but if it works it works bruh?
        # ANd yeah there are no things called access_token and token_type I'm cooked
        return LoginResponse(
            message="Login successful",
            access_token=access_token,
            token_type="bearer",
            user=user_response,
        ), None

    def get_user(self, user_id: int) -> Optional[UserResponse]:
        """
        Get a user by ID.

        Args:
            user_id: The user ID.

        Returns:
            UserResponse or None if not found.
        """
        user = self.user_repo.get(user_id)
        if not user:
            return None

        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """
        Get a user by email.

        Args:
            email: The user email.

        Returns:
            UserResponse or None if not found.
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            return None

        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: The user ID.

        Returns:
            True if deactivated, False if not found.
        """
        user = self.user_repo.update_user(user_id, is_active=False)
        if not user:
            return False

        logger.info(f"User deactivated: {user.email}")
        return True

    def activate_user(self, user_id: int) -> bool:
        """
        Activate a user account.

        Args:
            user_id: The user ID.

        Returns:
            True if activated, False if not found.
        """
        user = self.user_repo.update_user(user_id, is_active=True)
        if not user:
            return False

        logger.info(f"User activated: {user.email}")
        return True
