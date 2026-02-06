import asyncio
from datetime import datetime, timezone

from src.api.routes import snapshots as snapshots_route


def test_create_midpoint_snapshot_route_calls_service(monkeypatch):
    expected = {
        "snapshot_id": 10,
        "project_id": 5,
        "snapshot_type": "midpoint",
        "commit_hash": "abc",
        "commit_index": 1,
        "total_commits": 3,
        "created_at": datetime.now(timezone.utc),
        "summary": {"total_files": 2, "total_lines": 5, "top_extensions": [(".py", 2)]},
    }

    class FakeSnapshotService:
        def __init__(self, db):
            self.db = db

        def create_midpoint_snapshot(self, project_id: int):
            assert project_id == 5
            return expected

    monkeypatch.setattr(snapshots_route, "SnapshotService", FakeSnapshotService)

    result = asyncio.run(snapshots_route.create_midpoint_snapshot(project_id=5, db=object()))

    assert result == expected
