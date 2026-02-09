"""Snapshot service for commit-based snapshots."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import zipfile
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


@dataclass(frozen=True)
class CommitPoint:
    """Generic commit metadata for snapshotting."""

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
        return self._create_snapshot(project_id=project_id, snapshot_type="midpoint")

    def create_current_snapshot(self, project_id: int) -> dict:
        """Create a snapshot representing the uploaded project's current state."""
        return self._create_snapshot(project_id=project_id, snapshot_type="current")

    def create_current_and_midpoint_snapshots(self, project_id: int) -> dict:
        """Create both current and midpoint snapshots in one request."""
        project = self.project_repo.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            repo_root = self._materialize_repo(project.root_path, project.source_url, workspace)

            current_commit = self._resolve_commit_point(repo_root, snapshot_type="current")
            current_snapshot = self._build_snapshot(
                project_id, repo_root, current_commit, snapshot_type="current"
            )
            current_saved = self._persist_snapshot(project_id, current_snapshot)

            midpoint_commit = self._resolve_commit_point(repo_root, snapshot_type="midpoint")
            self._git(repo_root, "checkout", "--force", "--detach", midpoint_commit.hash)
            self._git(repo_root, "clean", "-fd")
            midpoint_snapshot = self._build_snapshot(
                project_id, repo_root, midpoint_commit, snapshot_type="midpoint"
            )
            midpoint_saved = self._persist_snapshot(project_id, midpoint_snapshot)

            return {
                "project_id": project_id,
                "current_snapshot": current_saved,
                "midpoint_snapshot": midpoint_saved,
            }

    def _create_snapshot(self, project_id: int, snapshot_type: str) -> dict:
        project = self.project_repo.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            repo_root = self._materialize_repo(project.root_path, project.source_url, workspace)
            commit_point = self._resolve_commit_point(repo_root, snapshot_type=snapshot_type)
            if snapshot_type == "midpoint":
                self._git(repo_root, "checkout", "--force", "--detach", commit_point.hash)
                self._git(repo_root, "clean", "-fd")
            snapshot = self._build_snapshot(project_id, repo_root, commit_point, snapshot_type=snapshot_type)
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
                self._extract_zip(zip_path, extracted)
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
        candidates = []
        if (base_path / ".git").is_dir():
            candidates.append(base_path)
        for git_dir in base_path.rglob(".git"):
            if git_dir.is_dir():
                candidates.append(git_dir.parent)
        for candidate in candidates:
            if self._is_valid_git_repo(candidate):
                return candidate
        return None

    def _is_valid_git_repo(self, path: Path) -> bool:
        """Check that the path contains a working git repository."""
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--git-dir"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.returncode == 0

    def _get_midpoint_commit(self, repo_root: Path) -> MidpointCommit:
        output = self._git(repo_root, "rev-list", "--reverse", "HEAD")
        commits = [line.strip() for line in output.splitlines() if line.strip()]
        if not commits:
            raise HTTPException(status_code=400, detail="No commits found in repository history.")
        midpoint_index = (len(commits) - 1) // 2
        return MidpointCommit(hash=commits[midpoint_index], index=midpoint_index, total_commits=len(commits))

    def _get_current_commit(self, repo_root: Path) -> CommitPoint:
        output = self._git(repo_root, "rev-list", "--reverse", "HEAD")
        commits = [line.strip() for line in output.splitlines() if line.strip()]
        if not commits:
            raise HTTPException(status_code=400, detail="No commits found in repository history.")
        current_index = len(commits) - 1
        return CommitPoint(hash=commits[current_index], index=current_index, total_commits=len(commits))

    def _resolve_commit_point(self, repo_root: Path, snapshot_type: str) -> CommitPoint:
        if snapshot_type == "midpoint":
            midpoint = self._get_midpoint_commit(repo_root)
            return CommitPoint(hash=midpoint.hash, index=midpoint.index, total_commits=midpoint.total_commits)
        if snapshot_type == "current":
            return self._get_current_commit(repo_root)
        raise HTTPException(status_code=400, detail=f"Unsupported snapshot type: {snapshot_type}")

    def _build_snapshot(self, project_id: int, repo_root: Path, commit_point: CommitPoint, snapshot_type: str) -> dict:
        commit_iso = self._git(repo_root, "show", "-s", "--format=%cI", commit_point.hash).strip()
        commit_message = self._git(repo_root, "show", "-s", "--format=%s", commit_point.hash).strip()

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
            "snapshot_type": snapshot_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "commit": {
                "hash": commit_point.hash,
                "index": commit_point.index,
                "total_commits": commit_point.total_commits,
                "ratio": round((commit_point.index + 1) / commit_point.total_commits, 4),
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

    def compare_snapshots(self, base_snapshot_id: int, target_snapshot_id: int) -> dict:
        """Compare two stored snapshots and return growth metrics."""
        base = self.snapshot_repo.get(base_snapshot_id)
        target = self.snapshot_repo.get(target_snapshot_id)

        if not base:
            raise HTTPException(status_code=404, detail=f"Snapshot not found: {base_snapshot_id}")
        if not target:
            raise HTTPException(status_code=404, detail=f"Snapshot not found: {target_snapshot_id}")
        if base.project_id != target.project_id:
            raise HTTPException(status_code=400, detail="Snapshots must belong to the same project.")

        base_payload = json.loads(base.payload_json)
        target_payload = json.loads(target.payload_json)
        base_summary = base_payload.get("summary", {})
        target_summary = target_payload.get("summary", {})

        base_files = int(base_summary.get("total_files", 0) or 0)
        target_files = int(target_summary.get("total_files", 0) or 0)
        base_lines = int(base_summary.get("total_lines", 0) or 0)
        target_lines = int(target_summary.get("total_lines", 0) or 0)

        files_delta = target_files - base_files
        lines_delta = target_lines - base_lines

        base_ext = self._extensions_to_map(base_summary.get("top_extensions", []))
        target_ext = self._extensions_to_map(target_summary.get("top_extensions", []))
        extension_deltas = []
        for ext in sorted(set(base_ext) | set(target_ext)):
            b = base_ext.get(ext, 0)
            t = target_ext.get(ext, 0)
            if b == t:
                continue
            extension_deltas.append(
                {
                    "extension": ext,
                    "base_count": b,
                    "target_count": t,
                    "delta": t - b,
                }
            )

        return {
            "base_snapshot_id": base.id,
            "target_snapshot_id": target.id,
            "project_id": base.project_id,
            "base_commit_hash": base.commit_hash,
            "target_commit_hash": target.commit_hash,
            "delta": {
                "files_delta": files_delta,
                "lines_delta": lines_delta,
                "files_growth_pct": self._growth_pct(base_files, target_files),
                "lines_growth_pct": self._growth_pct(base_lines, target_lines),
            },
            "extension_deltas": extension_deltas,
        }

    def _count_lines(self, file_path: Path) -> int:
        if file_path.suffix.lower() not in TEXT_EXTENSIONS:
            return 0
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except OSError:
            return 0

    @staticmethod
    def _growth_pct(base_value: int, target_value: int) -> float:
        if base_value == 0:
            if target_value == 0:
                return 0.0
            return 100.0
        return round(((target_value - base_value) / base_value) * 100.0, 2)

    @staticmethod
    def _extensions_to_map(items) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in items or []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                ext = str(item[0])
                try:
                    result[ext] = int(item[1])
                except (TypeError, ValueError):
                    result[ext] = 0
        return result

    @staticmethod
    def _extract_zip(zip_path: Path, dest: Path) -> None:
        """Extract ZIP while skipping macOS junk (__MACOSX, .DS_Store, ._ files)."""
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                if (
                    name.startswith("__MACOSX/") or "/__MACOSX/" in name
                    or Path(name).name == ".DS_Store"
                    or Path(name).name.startswith("._")
                ):
                    continue
                zf.extract(info, dest)

    def _git(self, repo_root: Path, *args: str) -> str:
        cmd = ["git", "-C", str(repo_root), *args]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Git command failed: {' '.join(args)}. {proc.stderr.strip()}",
            )
        return proc.stdout
