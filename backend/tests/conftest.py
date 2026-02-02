"""Pytest fixtures for testing."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.models.database import Base, get_db
from src.models.orm import Project, Language


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a test database session."""
    # Create in-memory SQLite database for testing
    # check_same_thread=False is needed for FastAPI async tests
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Use static pool for in-memory database
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def client(test_db: Session) -> TestClient:
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield test_db
        finally:
            # Don't close the session here, let test_db fixture handle it
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="function")
def sample_project(test_db: Session, temp_dir: Path) -> Project:
    """Create a sample project in the test database."""
    from datetime import datetime, timezone

    project = Project(
        name="test-project",
        root_path=str(temp_dir / "test-project"),
        source_type="github",
        source_url="https://github.com/test/repo",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        zip_uploaded_at=datetime.now(timezone.utc),
        first_file_created=datetime.now(timezone.utc),
        first_commit_date=datetime.now(timezone.utc),
        project_started_at=datetime.now(timezone.utc),
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)

    return project


@pytest.fixture(scope="function")
def git_repo_zip(temp_dir: Path) -> Path:
    """Create a sample ZIP file with git repository."""
    import subprocess
    import zipfile

    # Create a simple git repository
    repo_dir = temp_dir / "test-repo"
    repo_dir.mkdir()

    # Initialize git
    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        capture_output=True,
        check=True,
    )

    # Create initial file and commit
    (repo_dir / "README.md").write_text("# Test Project\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        capture_output=True,
        check=True,
    )

    # Create more commits (at least 10 for snapshot creation)
    for i in range(1, 15):
        file_path = repo_dir / f"file{i}.py"
        file_path.write_text(f"# File {i}\nprint('hello')\n")
        subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Add file{i}"],
            cwd=repo_dir,
            capture_output=True,
            check=True,
        )

    # Create ZIP file
    zip_path = temp_dir / "test-repo.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root_str, dirs, files in os.walk(repo_dir):
            root_path = Path(root_str)
            for file in files:
                file_path = root_path / file
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)

    return zip_path
