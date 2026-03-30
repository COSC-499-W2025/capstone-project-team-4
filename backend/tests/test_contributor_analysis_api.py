"""Tests for contributor analysis API endpoints."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_current_user
from src.api.main import app
from src.models.schemas.contributor import (
    AreaShareSchema,
    ContributorAnalysisDetailResponseSchema,
    ContributorAnalysisDetailSchema,
    ContributorDirectoriesResponseSchema,
    ContributorSummarySchema,
    TopDirectoryItemSchema,
    TopFileItemSchema,
)


@pytest.fixture
def client():
    """Create test client."""
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = no_lifespan
    app.dependency_overrides[get_current_user] = lambda: Mock(id=1, is_active=True)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.router.lifespan_context = original_lifespan


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def sample_analysis_response():
    """Sample contributor analysis response."""
    return ContributorAnalysisDetailResponseSchema(
        project_id=1,
        project_name="Demo Project",
        branch="HEAD",
        contributor=ContributorAnalysisDetailSchema(
            contributor_id=1,
            name="Demo User",
            summary=ContributorSummarySchema(
                top_areas=[
                    AreaShareSchema(area="backend", share=0.75),
                    AreaShareSchema(area="frontend", share=0.25),
                ],
                top_files=[
                    TopFileItemSchema(
                        file="backend/src/services/contributor_analysis_service.py",
                        lines_changed=420,
                    ),
                    TopFileItemSchema(
                        file="frontend/src/pages/Dashboard.jsx",
                        lines_changed=180,
                    ),
                ],
            ),
        ),
        generated_at=datetime(2026, 2, 9, tzinfo=timezone.utc),
    )


def test_get_contributor_analysis_success(client, mock_db_session, sample_analysis_response):
    """Test successful contributor analysis retrieval."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo, \
         patch("src.api.routes.contributor_analysis.ContributorRepository") as mock_contributor_repo, \
         patch("src.api.routes.contributor_analysis.ContributorAnalysisService") as mock_service:
        
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        
        # Mock project exists
        mock_project = Mock()
        mock_project.id = 1
        mock_project.user_id = 1
        mock_project_repo.return_value.get.return_value = mock_project
        
        # Mock contributor exists and belongs to project
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        # Mock analysis service
        mock_service.return_value.get_contributor_analysis.return_value = sample_analysis_response
        
        # Make request
        response = client.get("/api/projects/1/contributors/1/analysis")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == 1
        assert data["contributor"]["contributor_id"] == 1
        assert len(data["contributor"]["summary"]["top_areas"]) == 2
        assert data["contributor"]["summary"]["top_areas"][0]["area"] == "backend"
        assert data["contributor"]["summary"]["top_areas"][0]["share"] == 0.75
        assert len(data["contributor"]["summary"]["top_files"]) == 2
        assert "backend/src/services" in data["contributor"]["summary"]["top_files"][0]["file"]


def test_get_contributor_analysis_project_not_found(client, mock_db_session):
    """Test 404 when project does not exist."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo:
        
        mock_get_db.return_value = mock_db_session
        mock_project_repo.return_value.get.return_value = None
        
        response = client.get("/api/projects/999/contributors/1/analysis")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_get_contributor_analysis_contributor_not_found(client, mock_db_session):
    """Test 404 when contributor does not exist."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo, \
         patch("src.api.routes.contributor_analysis.ContributorRepository") as mock_contributor_repo:
        
        mock_get_db.return_value = mock_db_session
        
        # Project exists
        mock_project = Mock()
        mock_project.id = 1
        mock_project.user_id = 1
        mock_project_repo.return_value.get.return_value = mock_project
        
        # Contributor does not exist
        mock_contributor_repo.return_value.get.return_value = None
        
        response = client.get("/api/projects/1/contributors/999/analysis")
        
        assert response.status_code == 404
        assert "999" in response.json()["detail"]
        assert "not found" in response.json()["detail"].lower()


def test_get_contributor_analysis_contributor_wrong_project(client, mock_db_session):
    """Test 400 when contributor does not belong to the specified project."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo, \
         patch("src.api.routes.contributor_analysis.ContributorRepository") as mock_contributor_repo:
        
        mock_get_db.return_value = mock_db_session
        
        # Project exists
        mock_project = Mock()
        mock_project.id = 1
        mock_project.user_id = 1
        mock_project_repo.return_value.get.return_value = mock_project
        
        # Contributor exists but belongs to different project
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 2  # Different project
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        response = client.get("/api/projects/1/contributors/1/analysis")
        
        assert response.status_code == 400
        assert "does not belong to project" in response.json()["detail"]


def test_get_contributor_analysis_with_branch_parameter(client, mock_db_session, sample_analysis_response):
    """Test contributor analysis with specific branch parameter."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo, \
         patch("src.api.routes.contributor_analysis.ContributorRepository") as mock_contributor_repo, \
         patch("src.api.routes.contributor_analysis.ContributorAnalysisService") as mock_service:
        
        mock_get_db.return_value = mock_db_session
        
        # Setup mocks
        mock_project = Mock()
        mock_project.id = 1
        mock_project.user_id = 1
        mock_project_repo.return_value.get.return_value = mock_project
        
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        mock_service.return_value.get_contributor_analysis.return_value = sample_analysis_response
        
        # Make request with branch parameter
        response = client.get("/api/projects/1/contributors/1/analysis?branch=feature-branch")
        
        assert response.status_code == 200
        
        # Verify service was called with branch parameter
        mock_service.return_value.get_contributor_analysis.assert_called_once_with(
            project_id=1,
            contributor_id=1,
            branch="feature-branch",
        )


def test_get_contributor_analysis_service_returns_none(client, mock_db_session):
    """Test 500 when service returns None (analysis failed)."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo, \
         patch("src.api.routes.contributor_analysis.ContributorRepository") as mock_contributor_repo, \
         patch("src.api.routes.contributor_analysis.ContributorAnalysisService") as mock_service:
        
        mock_get_db.return_value = mock_db_session
        
        # Setup mocks
        mock_project = Mock()
        mock_project.id = 1
        mock_project.user_id = 1
        mock_project_repo.return_value.get.return_value = mock_project
        
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        # Service returns None
        mock_service.return_value.get_contributor_analysis.return_value = None
        
        response = client.get("/api/projects/1/contributors/1/analysis")
        
        assert response.status_code == 500
        assert "Failed to generate" in response.json()["detail"]


def test_get_contributor_analysis_service_raises_exception(client, mock_db_session):
    """Test 500 when service raises an unexpected exception."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo, \
         patch("src.api.routes.contributor_analysis.ContributorRepository") as mock_contributor_repo, \
         patch("src.api.routes.contributor_analysis.ContributorAnalysisService") as mock_service:
        
        mock_get_db.return_value = mock_db_session
        
        # Setup mocks
        mock_project = Mock()
        mock_project.id = 1
        mock_project.user_id = 1
        mock_project_repo.return_value.get.return_value = mock_project
        
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        # Service raises exception
        mock_service.return_value.get_contributor_analysis.side_effect = Exception("Git error")
        
        response = client.get("/api/projects/1/contributors/1/analysis")
        
        assert response.status_code == 500
        assert "Failed to analyze" in response.json()["detail"]


def test_get_contributor_analysis_invalid_branch_returns_400(client, mock_db_session):
    """Test 400 when service reports invalid branch."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo, \
         patch("src.api.routes.contributor_analysis.ContributorRepository") as mock_contributor_repo, \
         patch("src.api.routes.contributor_analysis.ContributorAnalysisService") as mock_service:

        mock_get_db.return_value = mock_db_session

        mock_project = Mock()
        mock_project.id = 1
        mock_project.user_id = 1
        mock_project_repo.return_value.get.return_value = mock_project

        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor

        mock_service.return_value.get_contributor_analysis.side_effect = ValueError(
            "Branch 'does-not-exist' does not exist"
        )

        response = client.get(
            "/api/projects/1/contributors/1/analysis?branch=does-not-exist"
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]


@pytest.fixture
def sample_directories_response():
    """Sample contributor directories response."""
    return ContributorDirectoriesResponseSchema(
        project_id=1,
        project_name="Demo Project",
        branch="HEAD",
        contributor_id=1,
        contributor_name="Demo User",
        top_directories=[
            TopDirectoryItemSchema(
                directory="backend/src/services",
                lines_changed=420,
                share=0.7,
                files_count=5,
            ),
            TopDirectoryItemSchema(
                directory="frontend/src/components",
                lines_changed=180,
                share=0.3,
                files_count=3,
            ),
        ],
        generated_at=datetime(2026, 2, 9, tzinfo=timezone.utc),
    )


def test_get_contributor_directories_success(client, mock_db_session, sample_directories_response):
    """Test successful contributor directories retrieval."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo, \
         patch("src.api.routes.contributor_analysis.ContributorRepository") as mock_contributor_repo, \
         patch("src.api.routes.contributor_analysis.ContributorAnalysisService") as mock_service:

        mock_get_db.return_value = mock_db_session

        mock_project = Mock()
        mock_project.id = 1
        mock_project.user_id = 1
        mock_project_repo.return_value.get.return_value = mock_project

        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor

        mock_service.return_value.get_contributor_directories.return_value = sample_directories_response

        response = client.get("/api/projects/1/contributors/1/directories?depth=3&top_n=5")

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == 1
        assert data["contributor_id"] == 1
        assert len(data["top_directories"]) == 2
        assert data["top_directories"][0]["directory"] == "backend/src/services"

        mock_service.return_value.get_contributor_directories.assert_called_once_with(
            project_id=1,
            contributor_id=1,
            branch=None,
            depth=3,
            top_n=5,
        )


def test_get_contributor_directories_invalid_branch_returns_400(client, mock_db_session):
    """Test 400 when directories service reports invalid branch."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo, \
         patch("src.api.routes.contributor_analysis.ContributorRepository") as mock_contributor_repo, \
         patch("src.api.routes.contributor_analysis.ContributorAnalysisService") as mock_service:

        mock_get_db.return_value = mock_db_session

        mock_project = Mock()
        mock_project.id = 1
        mock_project.user_id = 1
        mock_project_repo.return_value.get.return_value = mock_project

        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor

        mock_service.return_value.get_contributor_directories.side_effect = ValueError(
            "Branch 'does-not-exist' does not exist"
        )

        response = client.get(
            "/api/projects/1/contributors/1/directories?branch=does-not-exist"
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]
