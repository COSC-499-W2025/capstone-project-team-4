"""User repository for database operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.security import hash_password
from src.models.orm.user import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user operations."""

    def __init__(self, db: Session):
        """Initialize user repository."""
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def create_user(
        self,
        email: str,
        password: str,
        is_active: bool = True,
    ) -> User:
        """
        Create a new user with hashed password.

        Args:
            email: The user's email address.
            password: The plain-text password (will be hashed).
            is_active: Whether the user account is active.

        Returns:
            The created user.
        """
        user = User(
            email=email,
            password_hash=hash_password(password),
            is_active=is_active,
        )
        return self.create(user)

    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        password: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[User]:
        """
        Update an existing user.

        Args:
            user_id: The ID of the user to update.
            email: New email address (optional).
            password: New plain-text password (will be hashed, optional).
            is_active: New active status (optional).

        Returns:
            The updated user, or None if not found.
        """
        user = self.get(user_id)
        if not user:
            return None

        if email is not None:
            user.email = email
        if password is not None:
            user.password_hash = hash_password(password)
        if is_active is not None:
            user.is_active = is_active

        return self.update(user)

    def email_exists(self, email: str) -> bool:
        """Check if an email address is already registered."""
        return self.get_by_email(email) is not None
