"""Authentication API routes."""

import logging

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.user import UserCreate, UserResponse, UserLogin, LoginResponse
from src.models.orm.user import User
from src.services.auth_service import AuthService
from src.api.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from src.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.

    - Creates a new user with email and password
    - Email must be unique
    - Password must be at least 8 characters
    - Returns the created user (without password)
    """
    service = AuthService(db)
    user, error = service.register(data)

    if error:
        raise EmailAlreadyRegisteredError(data.email)

    return user


@router.post("/login", response_model=LoginResponse, summary="User Login")
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate a user.

    - Validates email and password
    - Returns user information on success
    """
    service = AuthService(db)
    login_data = UserLogin(email=data.username, password=data.password)
    response, error = service.authenticate(login_data)

    if error:
        raise InvalidCredentialsError(error)

    return response


# This is for testing `get_current_user` or that retrieval of the access token works
@router.get("/me", response_model=UserResponse, summary="Get Current User")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Test the endpoint to verify if the token actually validates.
    Returns the currently logged-in user
    """
    return current_user
