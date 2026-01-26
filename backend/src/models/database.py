"""Database connection and session management using SQLAlchemy."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from src.config.settings import settings

# Create SQLAlchemy base class
Base = declarative_base()

# Ensure data directory exists
settings.data_dir.mkdir(parents=True, exist_ok=True)

# Create engine with connection pooling for PostgreSQL
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Get database session as context manager for non-FastAPI use."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database by creating all tables."""
    # Import all models to ensure they're registered with Base
    from src.models.orm import (
        User,
        Project,
        ProjectAnalysisSummary,
        File,
        Language,
        Contributor,
        ContributorFile,
        Complexity,
        Skill,
        ProjectSkill,
        ProjectSkillTimeline,
        ResumeItem,
        Framework,
        ProjectFramework,
        Library,
        ProjectLibrary,
        Tool,
        ProjectTool,
        UserProfile,
        Experience,
        ExperienceType,
        DataPrivacySettings,
    )

    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables (use with caution)."""
    Base.metadata.drop_all(bind=engine)
