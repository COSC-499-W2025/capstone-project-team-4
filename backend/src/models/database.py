"""Database connection and session management using SQLAlchemy."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from src.config.settings import settings

# Create SQLAlchemy base class
Base = declarative_base()

# Ensure data directory exists (only relevant for local sqlite, but harmless to keep)
settings.data_dir.mkdir(parents=True, exist_ok=True)

# Get database URL from settings
_database_url = settings.database_url

# Configure connection args based on database type
connect_args = {}
if "sqlite" in str(_database_url):
    connect_args["check_same_thread"] = False

# Create engine with connection pooling
engine = create_engine(
    str(_database_url),
    echo=settings.database_echo,
    connect_args=connect_args,
    pool_pre_ping=True,
)

# Enable foreign key support ONLY for SQLite
# Postgres handles this natively, so we skip this block if not using sqlite
if "sqlite" in str(_database_url):

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Enable foreign key constraints for SQLite."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


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
