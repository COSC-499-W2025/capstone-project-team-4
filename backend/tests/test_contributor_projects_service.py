"""Tests for ContributorProjectsService."""

from types import SimpleNamespace
from datetime import date

import pytest
from fastapi import HTTPException

from src.services.contributor_projects_service import ContributorProjectsService


class MockContributorRepository:
    """Mock repository for contributor-project tuples."""

    def __init__(self, records, commit_rows=None):
        self._records = records
        self._commit_rows = commit_rows or []
        self.last_contributor_ids = None

    def get_all_with_projects(self):
        return self._records

    def get_commit_counts_by_day_for_contributors(self, contributor_ids):
        self.last_contributor_ids = contributor_ids
        return self._commit_rows


def _contributor(**kwargs):
    defaults = {
        "id": 1,
        "name": None,
        "email": None,
        "github_username": None,
        "github_email": None,
        "commits": 0,
        "total_lines_added": 0,
        "total_lines_deleted": 0,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _project(project_id: int, name: str):
    return SimpleNamespace(id=project_id, name=name)


def test_list_projects_by_github_username_aggregates_and_sorts():
    """Service aggregates identities per project and sorts by total_lines_changed."""
    records = [
        (
            _contributor(
                id=101,
                name="Slimosaurus",
                email="79215781+jaidenlo@users.noreply.github.com",
                github_username="jaidenlo",
                github_email="79215781+jaidenlo@users.noreply.github.com",
                commits=8,
                total_lines_added=700,
                total_lines_deleted=100,
            ),
            _project(10, "Capstone API"),
        ),
        (
            _contributor(
                id=102,
                name="Jaiden",
                email="jaidenlo@gmail.com",
                github_username=None,
                github_email=None,
                commits=6,
                total_lines_added=500,
                total_lines_deleted=200,
            ),
            _project(10, "Capstone API"),
        ),
        (
            _contributor(
                id=103,
                name="Jaiden",
                email="jaidenlo@gmail.com",
                github_username="jaidenlo",
                github_email=None,
                commits=3,
                total_lines_added=120,
                total_lines_deleted=30,
            ),
            _project(11, "Frontend UI"),
        ),
    ]

    service = ContributorProjectsService(db=None)
    service.contributor_repo = MockContributorRepository(records)

    result = service.list_projects_by_github_username("jaidenlo")

    assert result.github_username == "jaidenlo"
    assert result.total_projects == 2

    first = result.projects[0]
    second = result.projects[1]

    assert first.project_id == 10
    assert first.total_lines_changed == 1500
    assert first.commits == 14
    assert first.contributor_ids == [101, 102]

    assert second.project_id == 11
    assert second.total_lines_changed == 150


def test_list_projects_by_github_username_rejects_blank_username():
    """Service returns 400 for blank username."""
    service = ContributorProjectsService(db=None)
    service.contributor_repo = MockContributorRepository([])

    with pytest.raises(HTTPException) as exc:
        service.list_projects_by_github_username("   ")

    assert exc.value.status_code == 400
    assert "required" in exc.value.detail.lower()


def test_list_projects_by_github_username_not_found():
    """Service returns 404 when no matching contributors are found."""
    records = [
        (
            _contributor(
                id=201,
                name="Someone Else",
                email="someone@example.com",
                github_username="someone",
                commits=2,
                total_lines_added=10,
                total_lines_deleted=5,
            ),
            _project(20, "Other Project"),
        )
    ]

    service = ContributorProjectsService(db=None)
    service.contributor_repo = MockContributorRepository(records)

    with pytest.raises(HTTPException) as exc:
        service.list_projects_by_github_username("jaidenlo")

    assert exc.value.status_code == 404
    assert "No contributor records found" in exc.value.detail


def test_get_project_activity_heatmap_returns_grouped_days_for_matching_project():
    """Service returns commit counts by day for matching identities in one project only."""
    records = [
        (
            _contributor(
                id=101,
                name="Slimosaurus",
                email="79215781+jaidenlo@users.noreply.github.com",
                github_username="jaidenlo",
                github_email="79215781+jaidenlo@users.noreply.github.com",
            ),
            _project(10, "Capstone API"),
        ),
        (
            _contributor(
                id=102,
                name="Jaiden",
                email="jaidenlo@gmail.com",
            ),
            _project(10, "Capstone API"),
        ),
        (
            _contributor(
                id=103,
                name="Jaiden",
                email="jaidenlo@gmail.com",
                github_username="jaidenlo",
            ),
            _project(11, "Frontend UI"),
        ),
    ]

    commit_rows = [
        (date(2025, 9, 22), 2),
        (date(2025, 9, 23), 1),
    ]

    service = ContributorProjectsService(db=None)
    service.contributor_repo = MockContributorRepository(
        records, commit_rows=commit_rows
    )

    result = service.get_project_activity_heatmap("jaidenlo", 10)

    assert result.project_id == 10
    assert result.metric == "commits_per_day"
    assert len(result.data) == 2
    assert result.data[0].date == date(2025, 9, 22)
    assert result.data[0].count == 2
    assert result.data[1].date == date(2025, 9, 23)
    assert result.data[1].count == 1

    assert set(service.contributor_repo.last_contributor_ids) == {101, 102}


def test_get_project_activity_heatmap_rejects_blank_username():
    """Service returns 400 for blank username."""
    service = ContributorProjectsService(db=None)
    service.contributor_repo = MockContributorRepository([])

    with pytest.raises(HTTPException) as exc:
        service.get_project_activity_heatmap("   ", 10)

    assert exc.value.status_code == 400
    assert "required" in exc.value.detail.lower()


def test_get_project_activity_heatmap_not_found_for_project():
    """Service returns 404 when no matching contributor identity exists in that project."""
    records = [
        (
            _contributor(
                id=201,
                name="Someone Else",
                email="someone@example.com",
                github_username="someone",
            ),
            _project(20, "Other Project"),
        )
    ]

    service = ContributorProjectsService(db=None)
    service.contributor_repo = MockContributorRepository(records)

    with pytest.raises(HTTPException) as exc:
        service.get_project_activity_heatmap("jaidenlo", 20)

    assert exc.value.status_code == 404
    assert "No contributor activity found" in exc.value.detail


def test_get_project_activity_heatmap_returns_empty_data_when_no_commit_rows():
    """Service returns an empty heatmap when contributor matches but has no commit rows."""
    records = [
        (
            _contributor(
                id=101,
                name="Jaiden",
                email="jaidenlo@gmail.com",
                github_username="jaidenlo",
            ),
            _project(10, "Capstone API"),
        )
    ]

    service = ContributorProjectsService(db=None)
    service.contributor_repo = MockContributorRepository(records, commit_rows=[])

    result = service.get_project_activity_heatmap("jaidenlo", 10)

    assert result.project_id == 10
    assert result.metric == "commits_per_day"
    assert result.data == []
    assert service.contributor_repo.last_contributor_ids == [101]
