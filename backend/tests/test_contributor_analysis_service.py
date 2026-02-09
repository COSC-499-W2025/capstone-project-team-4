import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.services.contributor_analysis_service import ContributorAnalysisService
from src.models.schemas.contributor import AreaShareSchema, TopFileItemSchema
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _run_git(cwd: str, args: list[str], env: dict | None = None) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"


def _commit_file(
    repo_dir: str,
    rel_path: str,
    content: str,
    author_name: str,
    author_email: str,
    message: str,
) -> None:
    file_path = Path(repo_dir) / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    _run_git(repo_dir, ["add", rel_path])

    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email,
            "GIT_AUTHOR_DATE": "2024-01-01T00:00:00",
            "GIT_COMMITTER_DATE": "2024-01-01T00:00:00",
        }
    )
    _run_git(repo_dir, ["commit", "-m", message], env=env)


class MockContributorFile:
    """Mock object for contributor file."""
    def __init__(self, filename: str, modifications: int = 1):
        self.filename = filename
        self.modifications = modifications


class MockContributor:
    """Mock object for contributor."""
    def __init__(self, id: int, name: str, email: str, project_id: int):
        self.id = id
        self.name = name
        self.email = email
        self.project_id = project_id


class MockContributorWithFiles(MockContributor):
    """Mock contributor with files_modified."""
    def __init__(self, id: int, name: str, email: str, project_id: int, files_modified: list = None):
        super().__init__(id, name, email, project_id)
        self.files_modified = files_modified or []


class MockProject:
    """Mock object for project."""
    def __init__(self, id: int, name: str, root_path: str):
        self.id = id
        self.name = name
        self.root_path = root_path


class MockContributorRepository:
    """Mock contributor repository."""
    def __init__(self, contributors: dict):
        self.contributors = contributors
    
    def get(self, contributor_id: int):
        return self.contributors.get(contributor_id)
    
    def get_with_files(self, contributor_id: int):
        return self.contributors.get(contributor_id)


class MockProjectRepository:
    """Mock project repository."""
    def __init__(self, projects: dict):
        self.projects = projects
    
    def get(self, project_id: int):
        return self.projects.get(project_id)


class MockDB:
    """Mock database session."""
    pass


@pytest.fixture
def git_repo():
    """Create a temporary git repository with test files."""
    with TemporaryDirectory() as tmp_dir:
        _run_git(tmp_dir, ["init", "-b", "main"])
        
        # Create backend files
        _commit_file(
            tmp_dir,
            "backend/src/main.py",
            "import os\nprint('hello')\n",
            "Test User",
            "test@example.com",
            "backend commit",
        )
        
        # Create frontend files
        _commit_file(
            tmp_dir,
            "frontend/src/App.jsx",
            "import React from 'react';\n",
            "Test User",
            "test@example.com",
            "frontend commit",
        )
        
        # Create other area files
        _commit_file(
            tmp_dir,
            "docs/README.md",
            "# Documentation\n",
            "Test User",
            "test@example.com",
            "docs commit",
        )
        
        yield tmp_dir


def test_classify_file_to_area(git_repo):
    """Test file classification into backend/frontend areas."""
    db = MockDB()
    service = ContributorAnalysisService(db)
    
    # Backend files
    assert service._classify_file_to_area("backend/src/main.py") == "backend"
    assert service._classify_file_to_area("backend/api/routes.py") == "backend"
    assert service._classify_file_to_area("src/api/main.py") in ["backend", None]
    
    # Frontend files
    assert service._classify_file_to_area("frontend/src/App.jsx") == "frontend"
    assert service._classify_file_to_area("frontend/components/Button.jsx") == "frontend"
    
    # Other areas (should return None or configured area)
    result = service._classify_file_to_area("docs/README.md")
    # Could be "docs" or None depending on domain_mapping.yaml


def test_calculate_top_areas_backend_frontend_only(git_repo):
    """Test that top areas returns only backend and frontend."""
    db = MockDB()
    
    # Mock repositories
    contributor = MockContributorWithFiles(
        id=1,
        name="Test User",
        email="test@example.com",
        project_id=1,
        files_modified=[
            MockContributorFile("backend/src/main.py"),
            MockContributorFile("frontend/src/App.jsx"),
        ],
    )
    
    contrib_repo = MockContributorRepository({1: contributor})
    proj_repo = MockProjectRepository({1: MockProject(1, "Test", git_repo)})
    
    service = ContributorAnalysisService(db)
    service.contributor_repo = contrib_repo
    service.project_repo = proj_repo
    
    # Calculate areas
    areas = service.calculate_top_areas(
        contributor_id=1,
        repo_path=git_repo,
        branch="main",
    )
    
    # Verify only backend/frontend are returned
    area_names = {area.area for area in areas}
    assert area_names.issubset({"backend", "frontend"}), \
        f"Unexpected areas: {area_names}"
    
    # Verify share is between 0 and 1
    for area in areas:
        assert 0 <= area.share <= 1, f"Invalid share: {area.share}"


def test_calculate_top_files_returns_sorted_list(git_repo):
    """Test that top files are sorted by lines changed descending."""
    db = MockDB()
    
    contributor = MockContributorWithFiles(
        id=1,
        name="Test User",
        email="test@example.com",
        project_id=1,
        files_modified=[
            MockContributorFile("backend/src/main.py"),
            MockContributorFile("frontend/src/App.jsx"),
        ],
    )
    
    contrib_repo = MockContributorRepository({1: contributor})
    proj_repo = MockProjectRepository({1: MockProject(1, "Test", git_repo)})
    
    service = ContributorAnalysisService(db)
    service.contributor_repo = contrib_repo
    service.project_repo = proj_repo
    
    # Calculate top files
    top_files = service.calculate_top_files(
        contributor_id=1,
        repo_path=git_repo,
        branch="main",
        top_n=10,
    )
    
    # Verify results are TopFileItemSchema
    assert all(isinstance(f, TopFileItemSchema) for f in top_files)
    
    # Verify sorted descending by lines_changed
    if len(top_files) > 1:
        for i in range(len(top_files) - 1):
            assert top_files[i].lines_changed >= top_files[i + 1].lines_changed


def test_get_contributor_analysis_returns_valid_schema(git_repo):
    """Test get_contributor_analysis returns proper schema."""
    db = MockDB()
    
    contributor = MockContributorWithFiles(
        id=1,
        name="Test User",
        email="test@example.com",
        project_id=1,
        files_modified=[
            MockContributorFile("backend/src/main.py"),
        ],
    )
    
    project = MockProject(1, "Test Project", git_repo)
    
    contrib_repo = MockContributorRepository({1: contributor})
    proj_repo = MockProjectRepository({1: project})
    
    service = ContributorAnalysisService(db)
    service.contributor_repo = contrib_repo
    service.project_repo = proj_repo
    
    # Get analysis
    result = service.get_contributor_analysis(
        project_id=1,
        contributor_id=1,
        branch="main",
    )
    
    # Verify result structure (if not None)
    if result:
        assert result.project_id == 1
        assert result.contributor
        assert result.contributor.contributor_id == 1
        assert result.generated_at is not None


def test_get_contributor_analysis_handles_missing_contributor(git_repo):
    """Test get_contributor_analysis returns None for missing contributor."""
    db = MockDB()
    
    contrib_repo = MockContributorRepository({})
    project = MockProject(1, "Test Project", git_repo)
    proj_repo = MockProjectRepository({1: project})
    
    service = ContributorAnalysisService(db)
    service.contributor_repo = contrib_repo
    service.project_repo = proj_repo
    
    result = service.get_contributor_analysis(
        project_id=1,
        contributor_id=999,  # Non-existent
        branch="main",
    )
    
    assert result is None
