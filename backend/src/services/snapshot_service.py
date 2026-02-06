"""Snapshot service for commit-based snapshots."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.models.orm.project_snapshot import ProjectSnapshot
from src.repositories.project_repository import ProjectRepository
from src.repositories.snapshot_repository import SnapshotRepository

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
}

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".swift", ".kt", ".scala",
    ".sh", ".sql", ".html", ".css", ".scss", ".md", ".json", ".yaml",
    ".yml", ".toml", ".xml",
}


@dataclass(frozen=True)
class MidpointCommit:
    """Midpoint commit metadata."""

    hash: str
    index: int
    total_commits: int


class SnapshotService:
    """Generate midpoint snapshots and persist to database."""

    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.snapshot_repo = SnapshotRepository(db)

    def create_midpoint_snapshot(self, project_id: int) -> dict:
        project = self.project_repo.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            repo_root = self._materialize_repo(project.root_path, project.source_url, workspace)
            midpoint = self._get_midpoint_commit(repo_root)
            self._git(repo_root, "checkout", "--detach", midpoint.hash)
            snapshot = self._build_snapshot(project_id, repo_root, midpoint)
            return self._persist_snapshot(project_id, snapshot)

    def _materialize_repo(self, root_path: str, source_url: Optional[str], workspace: Path) -> Path:
        root = Path(root_path)
        if root.exists():
            copied = workspace / "repo"
            shutil.copytree(root, copied)
            git_root = self._find_git_root(copied)
            if git_root:
                return git_root

        if source_url:
            zip_path = Path(source_url)
            if zip_path.exists() and zip_path.suffix.lower() == ".zip":
                extracted = workspace / "unzipped"
                shutil.unpack_archive(str(zip_path), str(extracted))
                git_root = self._find_git_root(extracted)
                if git_root:
                    return git_root

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not locate a git repository for this project. "
                "Ensure uploaded ZIP includes .git and the stored ZIP still exists."
            ),
        )

    def _find_git_root(self, base_path: Path) -> Optional[Path]:
        if (base_path / ".git").exists():
            return base_path
        for git_dir in base_path.rglob(".git"):
            if git_dir.is_dir():
                return git_dir.parent
        return None

    def _get_midpoint_commit(self, repo_root: Path) -> MidpointCommit:
        output = self._git(repo_root, "rev-list", "--reverse", "HEAD")
        commits = [line.strip() for line in output.splitlines() if line.strip()]
        if not commits:
            raise HTTPException(status_code=400, detail="No commits found in repository history.")
        midpoint_index = (len(commits) - 1) // 2
        return MidpointCommit(hash=commits[midpoint_index], index=midpoint_index, total_commits=len(commits))

    def _build_snapshot(self, project_id: int, repo_root: Path, midpoint: MidpointCommit) -> dict:
        commit_iso = self._git(repo_root, "show", "-s", "--format=%cI", midpoint.hash).strip()
        commit_message = self._git(repo_root, "show", "-s", "--format=%s", midpoint.hash).strip()

        total_files = 0
        total_lines = 0
        extensions = Counter()
        for file_path in repo_root.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part in IGNORED_DIRS for part in file_path.parts):
                continue
            ext = file_path.suffix.lower() or "no_ext"
            extensions[ext] += 1
            total_files += 1
            total_lines += self._count_lines(file_path)

        return {
            "project_id": project_id,
            "snapshot_type": "midpoint",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "commit": {
                "hash": midpoint.hash,
                "index": midpoint.index,
                "total_commits": midpoint.total_commits,
                "ratio": round((midpoint.index + 1) / midpoint.total_commits, 4),
                "message": commit_message,
                "committed_at": commit_iso,
            },
            "summary": {
                "total_files": total_files,
                "total_lines": total_lines,
                "top_extensions": extensions.most_common(15),
            },
        }

    def _persist_snapshot(self, project_id: int, snapshot: dict) -> dict:
        row = ProjectSnapshot(
            project_id=project_id,
            snapshot_type=snapshot["snapshot_type"],
            commit_hash=snapshot["commit"]["hash"],
            commit_index=snapshot["commit"]["index"],
            total_commits=snapshot["commit"]["total_commits"],
            payload_json=json.dumps(snapshot),
        )
        saved = self.snapshot_repo.create(row)
        return {
            "snapshot_id": saved.id,
            "project_id": project_id,
            "snapshot_type": snapshot["snapshot_type"],
            "commit_hash": snapshot["commit"]["hash"],
            "commit_index": snapshot["commit"]["index"],
            "total_commits": snapshot["commit"]["total_commits"],
            "created_at": saved.created_at,
            "summary": snapshot["summary"],
        }

    def _count_lines(self, file_path: Path) -> int:
        if file_path.suffix.lower() not in TEXT_EXTENSIONS:
            return 0
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except OSError:
            return 0

    def _git(self, repo_root: Path, *args: str) -> str:
        cmd = ["git", "-C", str(repo_root), *args]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Git command failed: {' '.join(args)}. {proc.stderr.strip()}",
            )
        return proc.stdout

