"""FastAPI dependencies for dependency injection & auth."""

from sqlalchemy.orm import Session

from src.models.database import get_db
from src.services.analysis_service import AnalysisService
from src.services.project_service import ProjectService
from src.services.skill_service import SkillService
from src.services.resume_service import ResumeService

# Authentication imports
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from src.core.security import SECRET_KEY, ALGORITHM
from src.models.orm.user import User

# This is for FastAPI actually storing the session so that other API endpoints know!
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Validate the JWT token and retrieve current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials!",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Then get user from db
    db_query = select(User).where(User.id == int(user_id))
    user = db.scalar(db_query)

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


# Got to fix this because we need to have a fresh session for every request
def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    """Get analysis service instance."""
    return AnalysisService(db)


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    """Get project service instance."""
    return ProjectService(db)


def get_skill_service(db: Session = Depends(get_db)) -> SkillService:
    """Get skill service instance."""
    return SkillService(db)


def get_resume_service(db: Session = Depends(get_db)) -> ResumeService:
    """Get resume service instance."""
    return ResumeService(db)
