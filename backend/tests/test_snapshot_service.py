from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.services.snapshot_service import CommitPoint, MidpointCommit, SnapshotService


def test_create_midpoint_snapshot_raises_when_project_missing():
    service = SnapshotService(db=None)
    service.project_repo = SimpleNamespace(get=lambda _project_id: None)

    with pytest.raises(HTTPException) as exc:
        service.create_midpoint_snapshot(project_id=999)

    assert exc.value.status_code == 404


def test_get_midpoint_commit_picks_middle_hash(monkeypatch):
    service = SnapshotService(db=None)
    hashes = "\n".join(["a1", "b2", "c3", "d4", "e5"])
    monkeypatch.setattr(service, "_git", lambda _repo_root, *_args: hashes)

    midpoint = service._get_midpoint_commit(Path("/tmp/repo"))

    assert midpoint.hash == "c3"
    assert midpoint.index == 2
    assert midpoint.total_commits == 5


def test_build_snapshot_counts_files_and_ignores_dirs(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('a')\nprint('b')\n", encoding="utf-8")
    (repo / "notes.md").write_text("# title\n", encoding="utf-8")
    (repo / ".git").mkdir()
    (repo / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "pkg.js").write_text("const x=1;\n", encoding="utf-8")

    def fake_git(_repo_root, *args):
        if args == ("show", "-s", "--format=%cI", "abc123"):
            return "2026-02-06T00:00:00+00:00\n"
        if args == ("show", "-s", "--format=%s", "abc123"):
            return "midpoint commit\n"
        raise AssertionError(f"unexpected git call: {args}")

    service = SnapshotService(db=None)
    monkeypatch.setattr(service, "_git", fake_git)

    snapshot = service._build_snapshot(
        project_id=1,
        repo_root=repo,
        commit_point=CommitPoint(hash="abc123", index=1, total_commits=3),
        snapshot_type="midpoint",
    )

    assert snapshot["summary"]["total_files"] == 2
    assert snapshot["summary"]["total_lines"] == 3
    assert snapshot["commit"]["message"] == "midpoint commit"


def test_create_midpoint_snapshot_happy_path(monkeypatch):
    now = datetime.now(timezone.utc)
    service = SnapshotService(db=None)
    service.project_repo = SimpleNamespace(
        get=lambda _project_id: SimpleNamespace(root_path="/tmp/root", source_url="/tmp/u.zip")
    )
    service.snapshot_repo = SimpleNamespace(
        create=lambda obj: SimpleNamespace(id=44, created_at=now, **obj.__dict__)
    )

    monkeypatch.setattr(service, "_materialize_repo", lambda *_args, **_kwargs: Path("/tmp/repo"))
    monkeypatch.setattr(
        service, "_get_midpoint_commit", lambda *_args, **_kwargs: MidpointCommit(hash="h1", index=1, total_commits=3)
    )
    monkeypatch.setattr(service, "_git", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        service,
        "_build_snapshot",
        lambda *_args, **_kwargs: {
            "snapshot_type": "midpoint",
            "commit": {"hash": "h1", "index": 1, "total_commits": 3},
            "summary": {"total_files": 10, "total_lines": 20, "top_extensions": [(".py", 5)]},
        },
    )

    result = service.create_midpoint_snapshot(project_id=7)

    assert result["snapshot_id"] == 44
    assert result["project_id"] == 7
    assert result["snapshot_type"] == "midpoint"
    assert result["commit_hash"] == "h1"


def test_create_current_snapshot_happy_path(monkeypatch):
    now = datetime.now(timezone.utc)
    service = SnapshotService(db=None)
    service.project_repo = SimpleNamespace(
        get=lambda _project_id: SimpleNamespace(root_path="/tmp/root", source_url="/tmp/u.zip")
    )
    service.snapshot_repo = SimpleNamespace(
        create=lambda obj: SimpleNamespace(id=55, created_at=now, **obj.__dict__)
    )

    monkeypatch.setattr(service, "_materialize_repo", lambda *_args, **_kwargs: Path("/tmp/repo"))
    monkeypatch.setattr(
        service,
        "_resolve_commit_point",
        lambda *_args, **_kwargs: CommitPoint(hash="h2", index=2, total_commits=3),
    )
    monkeypatch.setattr(service, "_git", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        service,
        "_build_snapshot",
        lambda *_args, **_kwargs: {
            "snapshot_type": "current",
            "commit": {"hash": "h2", "index": 2, "total_commits": 3},
            "summary": {"total_files": 11, "total_lines": 21, "top_extensions": [(".py", 6)]},
        },
    )

    result = service.create_current_snapshot(project_id=8)

    assert result["snapshot_id"] == 55
    assert result["project_id"] == 8
    assert result["snapshot_type"] == "current"
    assert result["commit_hash"] == "h2"


def test_create_current_and_midpoint_snapshots_happy_path(monkeypatch):
    now = datetime.now(timezone.utc)
    service = SnapshotService(db=None)
    service.project_repo = SimpleNamespace(
        get=lambda _project_id: SimpleNamespace(root_path="/tmp/root", source_url="/tmp/u.zip")
    )
    saved_rows = [
        SimpleNamespace(id=100, created_at=now),
        SimpleNamespace(id=101, created_at=now),
    ]
    service.snapshot_repo = SimpleNamespace(
        create=lambda _obj: saved_rows.pop(0)
    )

    monkeypatch.setattr(service, "_materialize_repo", lambda *_args, **_kwargs: Path("/tmp/repo"))

    def fake_resolve(_repo_root, snapshot_type: str):
        if snapshot_type == "current":
            return CommitPoint(hash="curhash", index=4, total_commits=5)
        if snapshot_type == "midpoint":
            return CommitPoint(hash="midhash", index=2, total_commits=5)
        raise AssertionError("unexpected snapshot type")

    monkeypatch.setattr(service, "_resolve_commit_point", fake_resolve)
    monkeypatch.setattr(service, "_git", lambda *_args, **_kwargs: "")

    def fake_build(project_id, _repo_root, commit_point, snapshot_type):
        return {
            "snapshot_type": snapshot_type,
            "commit": {
                "hash": commit_point.hash,
                "index": commit_point.index,
                "total_commits": commit_point.total_commits,
            },
            "summary": {"total_files": 1, "total_lines": 2, "top_extensions": [(".py", 1)]},
        }

    monkeypatch.setattr(service, "_build_snapshot", fake_build)

    result = service.create_current_and_midpoint_snapshots(project_id=55)

    assert result["project_id"] == 55
    assert result["current_snapshot"]["snapshot_type"] == "current"
    assert result["current_snapshot"]["commit_hash"] == "curhash"
    assert result["midpoint_snapshot"]["snapshot_type"] == "midpoint"
    assert result["midpoint_snapshot"]["commit_hash"] == "midhash"
