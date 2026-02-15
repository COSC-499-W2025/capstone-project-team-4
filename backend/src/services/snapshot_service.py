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
from src.models.orm.snapshot_comparison import SnapshotComparison
from src.repositories.project_repository import ProjectRepository
from src.repositories.snapshot_comparison_repository import SnapshotComparisonRepository
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

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".swift", ".kt", ".scala", ".sh", ".sql",
}

TEXT_ONLY_EXTENSIONS = {".txt", ".md", ".rtf", ".csv"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp"}


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
        self.comparison_repo = SnapshotComparisonRepository(db)

    def delete_snapshot(self, project_id: int, snapshot_id: int) -> dict:
        """Delete a specific snapshot (and cascaded comparisons) by ID."""
        snapshot = self.snapshot_repo.get(snapshot_id)
        if not snapshot or snapshot.project_id != project_id:
            raise HTTPException(
                status_code=404,
                detail=f"Snapshot {snapshot_id} not found for project {project_id}.",
            )

        self.snapshot_repo.delete(snapshot_id)
        return {"project_id": project_id, "snapshot_id": snapshot_id}

    def create_midpoint_snapshot(self, project_id: int) -> dict:
        return self._create_snapshot(project_id=project_id, snapshot_type="midpoint")

    def create_current_snapshot(self, project_id: int) -> dict:
        """Create a snapshot representing the uploaded project's current state."""
        return self._create_snapshot(project_id=project_id, snapshot_type="current")

    def compare_current_and_midpoint(self, project_id: int) -> dict:
        """Compare the latest current and midpoint snapshots for a project.

        Returns a cached comparison if one exists for the same snapshot pair,
        otherwise computes and persists a new comparison.
        """
        current_snap = self.snapshot_repo.get_latest_for_project(project_id, "current")
        midpoint_snap = self.snapshot_repo.get_latest_for_project(project_id, "midpoint")
        if not current_snap or not midpoint_snap:
            raise HTTPException(
                status_code=404,
                detail="Both current and midpoint snapshots are required for comparison.",
            )

        # Return cached comparison if it exists for this snapshot pair
        cached = self.comparison_repo.get_by_snapshot_ids(current_snap.id, midpoint_snap.id)
        if cached:
            return json.loads(cached.payload_json)

        # Compute comparison
        comparison = self._build_comparison(project_id, current_snap, midpoint_snap)

        # Persist
        row = SnapshotComparison(
            project_id=project_id,
            current_snapshot_id=current_snap.id,
            midpoint_snapshot_id=midpoint_snap.id,
            payload_json=json.dumps(comparison),
        )
        self.comparison_repo.create(row)

        return comparison

    def _build_comparison(self, project_id: int, current_snap, midpoint_snap) -> dict:
        """Compute the delta between a current and midpoint snapshot."""
        current_payload = json.loads(current_snap.payload_json)
        midpoint_payload = json.loads(midpoint_snap.payload_json)

        cur_metrics = current_payload.get("summary", {}).get("analysis_metrics", {})
        mid_metrics = midpoint_payload.get("summary", {}).get("analysis_metrics", {})

        cur_summary = current_payload.get("summary", {})
        mid_summary = midpoint_payload.get("summary", {})

        def set_delta(key: str) -> dict:
            cur_set = set(cur_metrics.get(key, []))
            mid_set = set(mid_metrics.get(key, []))
            return {"added": sorted(cur_set - mid_set), "removed": sorted(mid_set - cur_set)}

        def count_delta(cur_val, mid_val) -> dict:
            return {"current": cur_val, "midpoint": mid_val, "delta": cur_val - mid_val}

        cur_complexity = cur_metrics.get("complexity_summary", {})
        mid_complexity = mid_metrics.get("complexity_summary", {})

        cur_counts = cur_metrics.get("counts", {})
        mid_counts = mid_metrics.get("counts", {})

        return {
            "project_id": project_id,
            "current_snapshot_id": current_snap.id,
            "midpoint_snapshot_id": midpoint_snap.id,
            "current_commit_hash": current_snap.commit_hash,
            "midpoint_commit_hash": midpoint_snap.commit_hash,
            "totals": {
                "total_files": count_delta(
                    cur_summary.get("total_files", 0), mid_summary.get("total_files", 0)
                ),
                "total_lines": count_delta(
                    cur_summary.get("total_lines", 0), mid_summary.get("total_lines", 0)
                ),
            },
            "counts": {
                k: count_delta(cur_counts.get(k, 0), mid_counts.get(k, 0))
                for k in ("language_count", "framework_count", "library_count", "tool_count", "skill_count")
            },
            "languages": set_delta("languages"),
            "skills": set_delta("skills"),
            "libraries": set_delta("libraries"),
            "frameworks": set_delta("frameworks"),
            "tools_and_technologies": set_delta("tools_and_technologies"),
            "complexity": {
                "total_functions": count_delta(
                    cur_complexity.get("total_functions", 0),
                    mid_complexity.get("total_functions", 0),
                ),
                "avg_complexity": {
                    "current": cur_complexity.get("avg_complexity", 0.0),
                    "midpoint": mid_complexity.get("avg_complexity", 0.0),
                    "delta": round(
                        cur_complexity.get("avg_complexity", 0.0)
                        - mid_complexity.get("avg_complexity", 0.0),
                        4,
                    ),
                },
                "max_complexity": count_delta(
                    cur_complexity.get("max_complexity", 0),
                    mid_complexity.get("max_complexity", 0),
                ),
                "high_complexity_count": count_delta(
                    cur_complexity.get("high_complexity_count", 0),
                    mid_complexity.get("high_complexity_count", 0),
                ),
            },
        }

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
        extension_counts = Counter()
        project_stats: dict[str, dict] = {}
        for file_path in repo_root.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part in IGNORED_DIRS for part in file_path.parts):
                continue

            rel = file_path.relative_to(repo_root)
            top_level = rel.parts[0] if len(rel.parts) > 1 else "__root__"
            stats = project_stats.setdefault(
                top_level,
                {
                    "project_name": top_level,
                    "file_count": 0,
                    "code_file_count": 0,
                    "text_file_count": 0,
                    "image_file_count": 0,
                    "other_file_count": 0,
                    "lines_of_code": 0,
                    "extension_counts": Counter(),
                },
            )

            ext = file_path.suffix.lower() or "no_ext"
            category = self._file_category(ext)
            line_count = self._count_lines(file_path)

            stats["file_count"] += 1
            stats[f"{category}_file_count"] += 1
            stats["lines_of_code"] += line_count
            stats["extension_counts"][ext] += 1

            total_files += 1
            total_lines += line_count
            extension_counts[ext] += 1

        project_breakdown = []
        content_type_totals = {
            "code_projects": 0,
            "text_projects": 0,
            "image_projects": 0,
            "mixed_projects": 0,
        }
        for name in sorted(project_stats):
            item = project_stats[name]
            content_type = self._project_content_type(item)
            content_type_totals[f"{content_type}_projects"] += 1
            project_breakdown.append(
                {
                    "project_name": item["project_name"],
                    "content_type": content_type,
                    "file_count": item["file_count"],
                    "code_file_count": item["code_file_count"],
                    "text_file_count": item["text_file_count"],
                    "image_file_count": item["image_file_count"],
                    "other_file_count": item["other_file_count"],
                    "lines_of_code": item["lines_of_code"],
                    "file_type_distribution": item["extension_counts"].most_common(10),
                }
            )

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
                "file_type_distribution": extension_counts.most_common(15),
                "project_breakdown": project_breakdown,
                "content_type_totals": content_type_totals,
                "analysis_metrics": self._collect_analysis_metrics(repo_root),
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

    def _collect_analysis_metrics(self, project_path: Path) -> dict:
        """Reuse existing analyzers to capture rich snapshot metrics."""
        from src.core.analyzers.project_stats import analyze_project, project_analysis_to_dict
        from src.core.detectors.framework import detect_frameworks_recursive
        from src.core.detectors.language import ProjectAnalyzer
        from src.core.detectors.library import detect_libraries_recursive
        from src.core.detectors.skill import analyze_project_skills
        from src.core.detectors.tool import detect_tools_recursive
        from src.core.utils.file_walker import collect_all_file_info
        from src.core.validators.cross_validator import CrossValidator

        try:
            file_info_list = collect_all_file_info(project_path, show_progress=False)
            file_paths = [f.path for f in file_info_list]
        except Exception:
            file_paths = []

        # Complexity
        complexity_summary = {
            "total_functions": 0,
            "avg_complexity": 0.0,
            "max_complexity": 0,
            "high_complexity_count": 0,
        }
        try:
            complexity_dict = project_analysis_to_dict(analyze_project(project_path, file_paths))
            complexities = [
                int(f.get("cyclomatic_complexity", 0))
                for f in complexity_dict.get("functions", [])
                if f.get("cyclomatic_complexity") is not None
            ]
            if complexities:
                complexity_summary = {
                    "total_functions": len(complexities),
                    "avg_complexity": round(sum(complexities) / len(complexities), 4),
                    "max_complexity": max(complexities),
                    "high_complexity_count": sum(1 for c in complexities if c >= 10),
                }
        except Exception:
            pass

        # Languages
        languages = []
        try:
            language_stats = ProjectAnalyzer().analyze_project_languages(str(project_path))
            languages = sorted([lang for lang, count in language_stats.items() if lang != "Unknown" and count > 0])
        except Exception:
            pass

        # Libraries and tools
        libraries_report = {"libraries": []}
        tools_report = {"tools": []}
        try:
            libraries_report = detect_libraries_recursive(project_path)
        except Exception:
            pass
        try:
            tools_report = detect_tools_recursive(project_path)
        except Exception:
            pass
        libraries = sorted({
            lib.get("name", "").strip()
            for lib in libraries_report.get("libraries", [])
            if lib.get("name")
        })
        tools = sorted({
            tool.get("name", "").strip()
            for tool in tools_report.get("tools", [])
            if tool.get("name")
        })

        # Frameworks via same detector + cross-validator flow as analysis service
        frameworks = []
        try:
            rules_path = Path(__file__).resolve().parent.parent / "core" / "rules" / "frameworks.yml"
            raw_fw = detect_frameworks_recursive(project_path, str(rules_path))
            per_folder = raw_fw.get("frameworks", {})
            fw_detected = []
            for folder_frameworks in per_folder.values():
                fw_detected.extend(folder_frameworks)
            validator = CrossValidator(
                languages=languages,
                frameworks=fw_detected,
                libraries=libraries_report.get("libraries", []),
                tools=tools_report.get("tools", []),
            )
            enhanced = validator.get_enhanced_results().get_all_frameworks()
            frameworks = sorted(set(f.get("name", "").strip() for f in enhanced if f.get("name")))
        except Exception:
            frameworks = []

        # Skills from existing skill extractor
        skills = []
        try:
            skill_report = analyze_project_skills(
                str(project_path),
                libraries=libraries_report.get("libraries", []),
                tools=tools_report.get("tools", []),
                languages=languages,
                frameworks=frameworks,
            )
            skill_categories = skill_report.get("skill_categories", {})
            skills = sorted({s for values in skill_categories.values() for s in values})
        except Exception:
            pass

        return {
            "languages": languages,
            "frameworks": frameworks,
            "libraries": libraries,
            "tools_and_technologies": tools,
            "skills": skills,
            "complexity_summary": complexity_summary,
            "counts": {
                "language_count": len(languages),
                "framework_count": len(frameworks),
                "library_count": len(libraries),
                "tool_count": len(tools),
                "skill_count": len(skills),
            },
        }

    @staticmethod
    def _file_category(ext: str) -> str:
        if ext in CODE_EXTENSIONS:
            return "code"
        if ext in TEXT_ONLY_EXTENSIONS:
            return "text"
        if ext in IMAGE_EXTENSIONS:
            return "image"
        return "other"

    @staticmethod
    def _project_content_type(stats: dict) -> str:
        active = sum(
            1
            for key in ("code_file_count", "text_file_count", "image_file_count")
            if stats.get(key, 0) > 0
        )
        if active >= 2:
            return "mixed"
        if stats.get("code_file_count", 0) > 0:
            return "code"
        if stats.get("text_file_count", 0) > 0:
            return "text"
        if stats.get("image_file_count", 0) > 0:
            return "image"
        return "mixed"

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
