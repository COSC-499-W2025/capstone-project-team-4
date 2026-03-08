"""Database connection and session management using SQLAlchemy."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, inspect, text
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
        ProjectSnapshot,
        ProjectThumbnail,
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
        Education,
        DataPrivacySettings,
        Portfolio,
    )

    Base.metadata.create_all(bind=engine)
    _repair_projects_table_schema()


def _repair_projects_table_schema() -> None:
    """Backfill optional `projects` columns for databases created before newer ORM fields.

    `create_all` does not alter existing tables. This lightweight repair avoids runtime
    `UndefinedColumn` errors in environments that skipped migrations.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "projects" not in tables:
        return

    existing_columns = {col["name"] for col in inspector.get_columns("projects")}
    statements: list[str] = []

    if "root_project_id" not in existing_columns:
        statements.append("ALTER TABLE projects ADD COLUMN root_project_id INTEGER")
    if "previous_project_id" not in existing_columns:
        statements.append("ALTER TABLE projects ADD COLUMN previous_project_id INTEGER")

    if not statements:
        return

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def drop_db() -> None:
    """Drop all database tables (use with caution)."""
    Base.metadata.drop_all(bind=engine)
