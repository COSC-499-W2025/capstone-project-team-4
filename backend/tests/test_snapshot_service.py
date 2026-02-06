from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.services.snapshot_service import MidpointCommit, SnapshotService


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
        midpoint=MidpointCommit(hash="abc123", index=1, total_commits=3),
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
