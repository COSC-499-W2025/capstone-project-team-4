"""Tests for ContributorRepository."""

from datetime import date
from unittest.mock import MagicMock

from src.repositories.contributor_repository import ContributorRepository


def test_get_commit_counts_by_day_for_contributors_returns_empty_without_query():
    """Repository returns [] and does not hit the database when no contributor IDs are given."""
    mock_db = MagicMock()
    repo = ContributorRepository(mock_db)

    result = repo.get_commit_counts_by_day_for_contributors([])

    assert result == []
    mock_db.execute.assert_not_called()


def test_get_commit_counts_by_day_for_contributors_executes_grouped_query_and_returns_rows():
    """Repository executes grouped day query and returns database rows unchanged."""
    mock_db = MagicMock()
    mock_execute_result = MagicMock()
    mock_execute_result.all.return_value = [
        (date(2025, 9, 22), 2),
        (date(2025, 9, 23), 1),
    ]
    mock_db.execute.return_value = mock_execute_result

    repo = ContributorRepository(mock_db)

    result = repo.get_commit_counts_by_day_for_contributors([101, 102])

    assert result == [
        (date(2025, 9, 22), 2),
        (date(2025, 9, 23), 1),
    ]

    mock_db.execute.assert_called_once()
    stmt = mock_db.execute.call_args.args[0]
    compiled_sql = str(stmt)

    assert "contributor_commits" in compiled_sql
    assert "commit_date" in compiled_sql
    assert "count" in compiled_sql.lower()
    assert "GROUP BY" in compiled_sql
    assert "ORDER BY" in compiled_sql