"""Tests for contributor analysis API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from src.api.main import app
from src.models.schemas.contributor import (
    ContributorAnalysisDetailResponseSchema,
    AreaShareSchema,
    TopFileItemSchema,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def sample_analysis_response():
    """Sample contributor analysis response."""
    return ContributorAnalysisDetailResponseSchema(
        contributor_id=1,
        top_areas=[
            AreaShareSchema(area="backend", share=75.5, lines_changed=1500),
            AreaShareSchema(area="frontend", share=24.5, lines_changed=490),
        ],
        top_files=[
            TopFileItemSchema(
                file_path="backend/src/services/contributor_analysis_service.py",
                lines_changed=420,
            ),
            TopFileItemSchema(
                file_path="frontend/src/pages/Dashboard.jsx",
                lines_changed=180,
            ),
        ],
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
        mock_project_repo.return_value.get.return_value = mock_project
        
        # Mock contributor exists and belongs to project
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        # Mock analysis service
        mock_service.return_value.get_contributor_analysis.return_value = sample_analysis_response
        
        # Make request
        response = client.get("/projects/1/contributors/1/analysis")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["contributor_id"] == 1
        assert len(data["top_areas"]) == 2
        assert data["top_areas"][0]["area"] == "backend"
        assert data["top_areas"][0]["share"] == 75.5
        assert len(data["top_files"]) == 2
        assert "backend/src/services" in data["top_files"][0]["file_path"]


def test_get_contributor_analysis_project_not_found(client, mock_db_session):
    """Test 404 when project does not exist."""
    with patch("src.api.routes.contributor_analysis.get_db") as mock_get_db, \
         patch("src.api.routes.contributor_analysis.ProjectRepository") as mock_project_repo:
        
        mock_get_db.return_value = mock_db_session
        mock_project_repo.return_value.get.return_value = None
        
        response = client.get("/projects/999/contributors/1/analysis")
        
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
        mock_project_repo.return_value.get.return_value = mock_project
        
        # Contributor does not exist
        mock_contributor_repo.return_value.get.return_value = None
        
        response = client.get("/projects/1/contributors/999/analysis")
        
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
        mock_project_repo.return_value.get.return_value = mock_project
        
        # Contributor exists but belongs to different project
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 2  # Different project
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        response = client.get("/projects/1/contributors/1/analysis")
        
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
        mock_project_repo.return_value.get.return_value = mock_project
        
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        mock_service.return_value.get_contributor_analysis.return_value = sample_analysis_response
        
        # Make request with branch parameter
        response = client.get("/projects/1/contributors/1/analysis?branch=feature-branch")
        
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
        mock_project_repo.return_value.get.return_value = mock_project
        
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        # Service returns None
        mock_service.return_value.get_contributor_analysis.return_value = None
        
        response = client.get("/projects/1/contributors/1/analysis")
        
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
        mock_project_repo.return_value.get.return_value = mock_project
        
        mock_contributor = Mock()
        mock_contributor.id = 1
        mock_contributor.project_id = 1
        mock_contributor_repo.return_value.get.return_value = mock_contributor
        
        # Service raises exception
        mock_service.return_value.get_contributor_analysis.side_effect = Exception("Git error")
        
        response = client.get("/projects/1/contributors/1/analysis")
        
        assert response.status_code == 500
        assert "Failed to analyze" in response.json()["detail"]
