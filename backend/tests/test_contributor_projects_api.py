"""Tests for contributor projects lookup API endpoint."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.main import app
from src.models.schemas.contributor import (
    ContributorIdentityMatchSchema,
    ContributorProjectLinesSchema,
    ContributorProjectsByUsernameResponseSchema,
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
def sample_projects_response():
    """Sample response for contributor projects endpoint."""
    return ContributorProjectsByUsernameResponseSchema(
        github_username="jaidenlo",
        total_projects=2,
        projects=[
            ContributorProjectLinesSchema(
                project_id=10,
                project_name="Capstone API",
                contributor_id=101,
                contributor_ids=[101, 102],
                commits=14,
                total_lines_added=1200,
                total_lines_deleted=300,
                total_lines_changed=1500,
                matched_identities=ContributorIdentityMatchSchema(
                    names=["Slimosaurus", "Jaiden"],
                    emails=["jaidenlo@gmail.com"],
                    github_usernames=["jaidenlo"],
                    github_emails=["79215781+jaidenlo@users.noreply.github.com"],
                ),
            ),
            ContributorProjectLinesSchema(
                project_id=11,
                project_name="Frontend UI",
                contributor_id=103,
                contributor_ids=[103],
                commits=5,
                total_lines_added=300,
                total_lines_deleted=50,
                total_lines_changed=350,
                matched_identities=ContributorIdentityMatchSchema(
                    names=["Jaiden"],
                    emails=["jaidenlo@gmail.com"],
                    github_usernames=["jaidenlo"],
                    github_emails=[],
                ),
            ),
        ],
    )


def test_get_projects_by_github_username_success(
    client, mock_db_session, sample_projects_response
):
    """Endpoint returns projects list for a matched GitHub username."""
    with (
        patch("src.api.routes.contributors.get_db") as mock_get_db,
        patch("src.api.routes.contributors.ContributorProjectsService") as mock_service,
    ):
        mock_get_db.return_value = mock_db_session
        mock_service.return_value.list_projects_by_github_username.return_value = (
            sample_projects_response
        )

        response = client.get("/api/contributors/github/jaidenlo/projects")

        assert response.status_code == 200
        data = response.json()
        assert data["github_username"] == "jaidenlo"
        assert data["total_projects"] == 2
        assert data["projects"][0]["project_id"] == 10
        assert data["projects"][0]["total_lines_changed"] == 1500

        mock_service.return_value.list_projects_by_github_username.assert_called_once_with(
            "jaidenlo"
        )


def test_get_projects_by_github_username_not_found(client, mock_db_session):
    """Endpoint returns 404 when username has no contributor records."""
    with (
        patch("src.api.routes.contributors.get_db") as mock_get_db,
        patch("src.api.routes.contributors.ContributorProjectsService") as mock_service,
    ):
        mock_get_db.return_value = mock_db_session
        mock_service.return_value.list_projects_by_github_username.side_effect = (
            HTTPException(
                status_code=404, detail="No contributor records found for unknown-user"
            )
        )

        response = client.get("/api/contributors/github/unknown-user/projects")

        assert response.status_code == 404
        assert "No contributor records found" in response.json()["detail"]
