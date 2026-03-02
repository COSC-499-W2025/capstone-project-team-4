"""Tests for async analysis endpoints (libraries, tools, frameworks)."""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
from contextlib import asynccontextmanager
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.models.database import get_db


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return MagicMock()


class TestAnalyzeLibrariesToolsEndpoint:
    """Tests for POST /{project_id}/analyze-libraries-tools endpoint."""

    def test_analyze_libraries_tools_project_not_found(self, client, mock_db_session):
        """Verify 404 when project doesn't exist."""
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            
            mock_get_db.return_value = mock_db_session
            
            # Mock service with no project found
            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/projects/analyze/999/analyze-libraries-tools")
            
            assert response.status_code == 404
            assert "Project not found" in response.json().get("detail", "")

    def test_analyze_libraries_tools_success(self, client, mock_db_session):
        """Verify successful library/tool analysis returns expected response."""
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            
            mock_get_db.return_value = mock_db_session
            
            # Mock project exists
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.root_path = "/tmp/project"
            mock_project.name = "test-project"
            
            # Mock service
            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_libraries_and_tools.return_value = {
                "project_id": 1,
                "libraries_found": 5,
                "tools_found": 3,
                "duration_seconds": 2.5,
            }
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/projects/analyze/1/analyze-libraries-tools")
            
            assert response.status_code == 200
            data = response.json()
            assert data["project_id"] == 1
            assert data["libraries_found"] == 5
            assert data["tools_found"] == 3
            assert data["duration_seconds"] == 2.5

    def test_analyze_libraries_tools_service_error(self, client, mock_db_session):
        """Verify proper error handling when service fails."""
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            
            mock_get_db.return_value = mock_db_session
            
            # Mock project exists but service fails
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.root_path = "/tmp/project"
            
            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_libraries_and_tools.side_effect = Exception("Analysis failed")
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/projects/analyze/1/analyze-libraries-tools")
            
            # Should return 400-level error on service failure
            assert response.status_code in [400, 422, 500]


class TestAnalyzeFrameworksEndpoint:
    """Tests for POST /{project_id}/analyze-frameworks endpoint."""

    def test_analyze_frameworks_project_not_found(self, client, mock_db_session):
        """Verify 404 when project doesn't exist."""
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            
            mock_get_db.return_value = mock_db_session
            
            # Mock service with no project found
            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/projects/analyze/999/analyze-frameworks")
            
            assert response.status_code == 404
            assert "Project not found" in response.json().get("detail", "")

    def test_analyze_frameworks_success(self, client, mock_db_session):
        """Verify successful framework analysis returns expected response."""
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            
            mock_get_db.return_value = mock_db_session
            
            # Mock project exists
            mock_project = MagicMock()
            mock_project.id = 2
            mock_project.root_path = "/tmp/project"
            mock_project.name = "test-project"
            
            # Mock service
            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_frameworks.return_value = {
                "project_id": 2,
                "frameworks_found": 4,
                "duration_seconds": 1.8,
            }
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/projects/analyze/2/analyze-frameworks")
            
            assert response.status_code == 200
            data = response.json()
            assert data["project_id"] == 2
            assert data["frameworks_found"] == 4
            assert data["duration_seconds"] == 1.8

    def test_analyze_frameworks_service_error(self, client, mock_db_session):
        """Verify proper error handling when service fails."""
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            
            mock_get_db.return_value = mock_db_session
            
            # Mock project exists but service fails
            mock_project = MagicMock()
            mock_project.id = 2
            mock_project.root_path = "/tmp/project"
            
            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_frameworks.side_effect = Exception("Framework analysis failed")
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/projects/analyze/2/analyze-frameworks")
            
            # Should return 400-level error on service failure
            assert response.status_code in [400, 422, 500]


class TestAsyncEndpointValidation:
    """Tests for input validation and error handling."""

    def test_invalid_project_id_libraries_tools(self, client):
        """Verify endpoint handles invalid project ID format."""
        response = client.post("/api/projects/analyze/invalid/analyze-libraries-tools")
        # Should get 422 (validation error) for non-integer project_id
        assert response.status_code == 422

    def test_invalid_project_id_frameworks(self, client):
        """Verify endpoint handles invalid project ID format."""
        response = client.post("/api/projects/analyze/invalid/analyze-frameworks")
        # Should get 422 (validation error) for non-integer project_id
        assert response.status_code == 422

    def test_negative_project_id_libraries_tools(self, client):
        """Verify endpoint handles negative project ID."""
        response = client.post("/api/projects/analyze/-1/analyze-libraries-tools")
        # Implementation dependent; may be 404 or 422
        assert response.status_code in [404, 422, 500]

    def test_negative_project_id_frameworks(self, client):
        """Verify endpoint handles negative project ID."""
        response = client.post("/api/projects/analyze/-1/analyze-frameworks")
        # Implementation dependent; may be 404 or 422
        assert response.status_code in [404, 422, 500]


class TestAsyncEndpointResponse:
    """Tests for endpoint response format."""

    def test_libraries_tools_response_format(self, client, mock_db_session):
        """Verify response format for libraries/tools endpoint."""
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            
            mock_get_db.return_value = mock_db_session
            
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.root_path = "/tmp/project"
            
            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_libraries_and_tools.return_value = {
                "project_id": 1,
                "libraries_found": 10,
                "tools_found": 5,
                "duration_seconds": 3.2,
            }
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/projects/analyze/1/analyze-libraries-tools")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "project_id" in data
            assert "libraries_found" in data
            assert "tools_found" in data
            assert "duration_seconds" in data
            
            # Verify data types
            assert isinstance(data["project_id"], int)
            assert isinstance(data["libraries_found"], int)
            assert isinstance(data["tools_found"], int)
            assert isinstance(data["duration_seconds"], float)

    def test_frameworks_response_format(self, client, mock_db_session):
        """Verify response format for frameworks endpoint."""
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            
            mock_get_db.return_value = mock_db_session
            
            mock_project = MagicMock()
            mock_project.id = 2
            mock_project.root_path = "/tmp/project"
            
            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_frameworks.return_value = {
                "project_id": 2,
                "frameworks_found": 7,
                "duration_seconds": 2.1,
            }
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/projects/analyze/2/analyze-frameworks")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "project_id" in data
            assert "frameworks_found" in data
            assert "duration_seconds" in data
            
            # Verify data types
            assert isinstance(data["project_id"], int)
            assert isinstance(data["frameworks_found"], int)
            assert isinstance(data["duration_seconds"], float)


class TestUnifiedTechStackEndpoints:
    """Tests for unified project/contributor tech stack endpoints."""

    def test_analyze_project_tech_stack_success(self, client, mock_db_session):
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            mock_get_db.return_value = mock_db_session

            mock_project = MagicMock()
            mock_project.id = 10
            mock_project.root_path = "/tmp/project"
            mock_project.source_url = "/tmp/project.zip"

            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_tech_stack.return_value = {
                "project_id": 10,
                "scope": "project",
                "libraries_found": 12,
                "frameworks_found": 4,
                "libraries": ["fastapi", "pydantic"],
                "frameworks": ["FastAPI"],
                "duration_seconds": 1.2,
            }
            mock_service_class.return_value = mock_service

            response = client.post("/api/projects/analyze/10/analyze-tech-stack")

            assert response.status_code == 200
            data = response.json()
            assert data["project_id"] == 10
            assert data["scope"] == "project"
            assert "libraries" in data
            assert "frameworks" in data

    def test_analyze_contributor_tech_stack_success(self, client, mock_db_session):
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            mock_get_db.return_value = mock_db_session

            mock_project = MagicMock()
            mock_project.id = 10
            mock_project.root_path = "/tmp/project"
            mock_project.source_url = "/tmp/project.zip"

            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_contributor_tech_stack.return_value = {
                "project_id": 10,
                "contributor_id": 7,
                "scope": "contributor",
                "files_considered": 18,
                "include_transitive": False,
                "libraries_found": 5,
                "frameworks_found": 2,
                "libraries": ["axios"],
                "frameworks": ["React"],
                "duration_seconds": 0.9,
            }
            mock_service_class.return_value = mock_service

            response = client.post("/api/projects/analyze/10/contributors/7/analyze-tech-stack")

            assert response.status_code == 200
            data = response.json()
            assert data["project_id"] == 10
            assert data["contributor_id"] == 7
            assert data["scope"] == "contributor"
            assert "files_considered" in data
            assert data["include_transitive"] is False

    def test_analyze_contributor_tech_stack_with_transitive(self, client, mock_db_session):
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            mock_get_db.return_value = mock_db_session

            mock_project = MagicMock()
            mock_project.id = 10
            mock_project.root_path = "/tmp/project"
            mock_project.source_url = "/tmp/project.zip"

            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_contributor_tech_stack.return_value = {
                "project_id": 10,
                "contributor_id": 7,
                "scope": "contributor",
                "files_considered": 18,
                "include_transitive": True,
                "libraries_found": 50,
                "frameworks_found": 2,
                "libraries": ["@babel/core", "axios"],
                "frameworks": ["React"],
                "duration_seconds": 1.5,
            }
            mock_service_class.return_value = mock_service

            response = client.post("/api/projects/analyze/10/contributors/7/analyze-tech-stack?include_transitive=true")

            assert response.status_code == 200
            data = response.json()
            assert data["include_transitive"] is True

    def test_analyze_contributor_tech_stack_contributor_not_found(self, client, mock_db_session):
        with patch("src.api.routes.analysis.get_db") as mock_get_db, \
             patch("src.api.routes.analysis.AnalysisService") as mock_service_class:
            mock_get_db.return_value = mock_db_session

            mock_project = MagicMock()
            mock_project.id = 11
            mock_project.root_path = "/tmp/project"
            mock_project.source_url = "/tmp/project.zip"

            from fastapi import HTTPException

            mock_service = MagicMock()
            mock_service.project_repo.get.return_value = mock_project
            mock_service.analyze_contributor_tech_stack.side_effect = HTTPException(
                status_code=404,
                detail="Contributor not found: 999",
            )
            mock_service_class.return_value = mock_service

            response = client.post("/api/projects/analyze/11/contributors/999/analyze-tech-stack")

            assert response.status_code == 404
            assert "Contributor not found" in response.json().get("detail", "")
