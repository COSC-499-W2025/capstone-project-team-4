import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from src.api.routes import snapshots as snapshots_route
from src.services.project_service import ProjectService


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
            "summary": {
                "total_files": 10,
                "total_lines": 50,
                "file_type_distribution": [(".py", 5)],
            },
        },
        "midpoint_snapshot": {
            "snapshot_id": 21,
            "project_id": 7,
            "snapshot_type": "midpoint",
            "commit_hash": "mid",
            "commit_index": 2,
            "total_commits": 5,
            "created_at": now,
            "summary": {
                "total_files": 8,
                "total_lines": 30,
                "file_type_distribution": [(".py", 4)],
            },
        },
    }

    class FakeSnapshotService:
        def __init__(self, db):
            self.db = db

        def create_current_and_midpoint_snapshots(
            self,
            project_id: int,
            percentage: int,
            end_percentage: int,
        ):
            assert project_id == 7
            assert percentage == 50
            assert end_percentage == 100
            return expected

    monkeypatch.setattr(snapshots_route, "SnapshotService", FakeSnapshotService)
    monkeypatch.setattr(ProjectService, "user_owns_project", lambda *_: True)
    result = asyncio.run(
        snapshots_route.create_current_and_midpoint_snapshots(
            project_id=7,
            percentage=50,
            end_percentage=100,
            db=object(),
            current_user=SimpleNamespace(id=1),
        )
    )

    assert result == expected


def test_delete_snapshot_route_calls_service(monkeypatch):
    expected = {"project_id": 7, "snapshot_id": 10}

    class FakeSnapshotService:
        def __init__(self, db):
            self.db = db

        def delete_snapshot(self, project_id: int, snapshot_id: int):
            assert project_id == 7
            assert snapshot_id == 10
            return expected

    monkeypatch.setattr(snapshots_route, "SnapshotService", FakeSnapshotService)
    monkeypatch.setattr(ProjectService, "user_owns_project", lambda *_: True)
    result = asyncio.run(
        snapshots_route.delete_snapshot(
            project_id=7,
            snapshot_id=10,
            db=object(),
            current_user=SimpleNamespace(id=1),
        )
    )

    assert result == expected


def test_compare_current_and_midpoint_snapshots_route_calls_service(monkeypatch):
    expected = {
        "project_id": 7,
        "current_snapshot_id": 20,
        "midpoint_snapshot_id": 21,
        "current_commit_hash": "cur",
        "midpoint_commit_hash": "mid",
        "totals": {
            "files": {"current": 10, "midpoint": 8, "delta": 2},
            "lines": {"current": 50, "midpoint": 30, "delta": 20},
        },
        "counts": {
            "languages": {"current": 2, "midpoint": 1, "delta": 1},
            "skills": {"current": 3, "midpoint": 2, "delta": 1},
            "libraries": {"current": 3, "midpoint": 1, "delta": 2},
            "frameworks": {"current": 1, "midpoint": 1, "delta": 0},
            "tools_and_technologies": {"current": 1, "midpoint": 0, "delta": 1},
        },
        "languages": {"added": ["JavaScript"], "removed": []},
        "skills": {"added": ["Automation"], "removed": []},
        "libraries": {"added": ["sqlalchemy"], "removed": []},
        "frameworks": {"added": [], "removed": []},
        "tools_and_technologies": {"added": ["Docker"], "removed": []},
        "complexity": {
            "total_functions": {"current": 25, "midpoint": 20, "delta": 5},
            "avg_complexity": {"current": 2.0, "midpoint": 1.5, "delta": 0.5},
            "max_complexity": {"current": 8, "midpoint": 6, "delta": 2},
            "high_complexity_count": {"current": 1, "midpoint": 0, "delta": 1},
        },
    }

    class FakeSnapshotService:
        def __init__(self, db):
            self.db = db

        def compare_current_and_midpoint(self, project_id: int):
            assert project_id == 7
            return expected

    monkeypatch.setattr(snapshots_route, "SnapshotService", FakeSnapshotService)
    monkeypatch.setattr(ProjectService, "user_owns_project", lambda *_: True)
    result = asyncio.run(
        snapshots_route.compare_current_and_midpoint_snapshots(
            project_id=7,
            db=object(),
            current_user=SimpleNamespace(id=1),
        )
    )
    assert result == expected
