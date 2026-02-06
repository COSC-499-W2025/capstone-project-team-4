import asyncio
from datetime import datetime, timezone

from src.api.routes import snapshots as snapshots_route


def test_create_current_and_midpoint_snapshots_route_calls_service(monkeypatch):
    now = datetime.now(timezone.utc)
    expected = {
        "project_id": 7,
        "current_snapshot": {
            "snapshot_id": 20,
            "project_id": 7,
            "snapshot_type": "current",
            "commit_hash": "cur",
            "commit_index": 4,
            "total_commits": 5,
            "created_at": now,
            "summary": {"total_files": 10, "total_lines": 50, "top_extensions": [(".py", 5)]},
        },
        "midpoint_snapshot": {
            "snapshot_id": 21,
            "project_id": 7,
            "snapshot_type": "midpoint",
            "commit_hash": "mid",
            "commit_index": 2,
            "total_commits": 5,
            "created_at": now,
            "summary": {"total_files": 8, "total_lines": 30, "top_extensions": [(".py", 4)]},
        },
    }

    class FakeSnapshotService:
        def __init__(self, db):
            self.db = db

        def create_current_and_midpoint_snapshots(self, project_id: int):
            assert project_id == 7
            return expected

    monkeypatch.setattr(snapshots_route, "SnapshotService", FakeSnapshotService)
    result = asyncio.run(snapshots_route.create_current_and_midpoint_snapshots(project_id=7, db=object()))

    assert result == expected
