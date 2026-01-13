"""FastAPI dependencies for dependency injection."""

from typing import Generator

from sqlalchemy.orm import Session

from src.models.database import SessionLocal, get_db
from src.services.analysis_service import AnalysisService
from src.services.project_service import ProjectService
from src.services.skill_service import SkillService
from src.services.resume_service import ResumeService


def get_analysis_service(db: Session = next(get_db())) -> AnalysisService:
    """Get analysis service instance."""
    return AnalysisService(db)


def get_project_service(db: Session = next(get_db())) -> ProjectService:
    """Get project service instance."""
    return ProjectService(db)


def get_skill_service(db: Session = next(get_db())) -> SkillService:
    """Get skill service instance."""
    return SkillService(db)


def get_resume_service(db: Session = next(get_db())) -> ResumeService:
    """Get resume service instance."""
    return ResumeService(db)
