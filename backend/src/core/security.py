"""Password hashing and verification utilities using bcrypt."""

import bcrypt
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Union

# This is for token creation
from jose import jwt

# Config for generating tokens, if there's none in the .env file, just use the default secret
# NOTE: In the .env file, it needs to be called SECRET_TOKEN
SECRET_KEY = os.getenv("SECRET_TOKEN", "DEFAULT_SECRET")
ALGORITHM = "HS256"
# For now, just make it expire in 30 mins
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        password: The plain-text password to hash.

    Returns:
        The hashed password string.
    """
    # Encode the password to bytes and generate salt
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.

    Args:
        plain_password: The plain-text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# Generate a JWT token for a user
def create_access_token(subject: Union[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
