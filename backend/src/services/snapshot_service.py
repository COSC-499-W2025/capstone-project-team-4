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
            self._git(repo_root, "checkout", "--detach", midpoint_commit.hash)
            midpoint_snapshot = self._build_snapshot(
                project_id, repo_root, midpoint_commit, snapshot_type="midpoint"
            )
            midpoint_saved = self._persist_snapshot(project_id, midpoint_snapshot)

            return {
                "project_id": project_id,
                "current_snapshot": current_saved,
                "midpoint_snapshot": midpoint_saved,
            }

    def compare_current_and_midpoint(self, project_id: int) -> dict:
        """Compare latest current snapshot with latest midpoint snapshot for a project."""
        current = self.snapshot_repo.get_latest_for_project(project_id, snapshot_type="current")
        midpoint = self.snapshot_repo.get_latest_for_project(project_id, snapshot_type="midpoint")
        if not current:
            raise HTTPException(status_code=404, detail=f"Current snapshot not found for project {project_id}")
        if not midpoint:
            raise HTTPException(status_code=404, detail=f"Midpoint snapshot not found for project {project_id}")

        current_payload = json.loads(current.payload_json)
        midpoint_payload = json.loads(midpoint.payload_json)
        current_summary = current_payload.get("summary", {})
        midpoint_summary = midpoint_payload.get("summary", {})
        current_metrics = current_summary.get("analysis_metrics", {})
        midpoint_metrics = midpoint_summary.get("analysis_metrics", {})

        current_files = int(current_summary.get("total_files", 0) or 0)
        midpoint_files = int(midpoint_summary.get("total_files", 0) or 0)
        current_lines = int(current_summary.get("total_lines", 0) or 0)
        midpoint_lines = int(midpoint_summary.get("total_lines", 0) or 0)

        current_counts = current_metrics.get("counts", {}) or {}
        midpoint_counts = midpoint_metrics.get("counts", {}) or {}

        current_complexity = current_metrics.get("complexity_summary", {}) or {}
        midpoint_complexity = midpoint_metrics.get("complexity_summary", {}) or {}

        return {
            "project_id": project_id,
            "current_snapshot_id": current.id,
            "midpoint_snapshot_id": midpoint.id,
            "current_commit_hash": current.commit_hash,
            "midpoint_commit_hash": midpoint.commit_hash,
            "totals": {
                "files": self._count_delta(current_files, midpoint_files),
                "lines": self._count_delta(current_lines, midpoint_lines),
            },
            "counts": {
                "languages": self._count_delta(
                    int(current_counts.get("language_count", 0) or 0),
                    int(midpoint_counts.get("language_count", 0) or 0),
                ),
                "skills": self._count_delta(
                    int(current_counts.get("skill_count", 0) or 0),
                    int(midpoint_counts.get("skill_count", 0) or 0),
                ),
                "libraries": self._count_delta(
                    int(current_counts.get("library_count", 0) or 0),
                    int(midpoint_counts.get("library_count", 0) or 0),
                ),
                "frameworks": self._count_delta(
                    int(current_counts.get("framework_count", 0) or 0),
                    int(midpoint_counts.get("framework_count", 0) or 0),
                ),
                "tools_and_technologies": self._count_delta(
                    int(current_counts.get("tool_count", 0) or 0),
                    int(midpoint_counts.get("tool_count", 0) or 0),
                ),
            },
            "languages": self._set_delta(
                current_metrics.get("languages", []), midpoint_metrics.get("languages", [])
            ),
            "skills": self._set_delta(
                current_metrics.get("skills", []), midpoint_metrics.get("skills", [])
            ),
            "libraries": self._set_delta(
                current_metrics.get("libraries", []), midpoint_metrics.get("libraries", [])
            ),
            "frameworks": self._set_delta(
                current_metrics.get("frameworks", []), midpoint_metrics.get("frameworks", [])
            ),
            "tools_and_technologies": self._set_delta(
                current_metrics.get("tools_and_technologies", []),
                midpoint_metrics.get("tools_and_technologies", []),
            ),
            "complexity": {
                "total_functions": self._count_delta(
                    int(current_complexity.get("total_functions", 0) or 0),
                    int(midpoint_complexity.get("total_functions", 0) or 0),
                ),
                "avg_complexity": {
                    "current": float(current_complexity.get("avg_complexity", 0.0) or 0.0),
                    "midpoint": float(midpoint_complexity.get("avg_complexity", 0.0) or 0.0),
                    "delta": round(
                        float(current_complexity.get("avg_complexity", 0.0) or 0.0)
                        - float(midpoint_complexity.get("avg_complexity", 0.0) or 0.0),
                        4,
                    ),
                },
                "max_complexity": self._count_delta(
                    int(current_complexity.get("max_complexity", 0) or 0),
                    int(midpoint_complexity.get("max_complexity", 0) or 0),
                ),
                "high_complexity_count": self._count_delta(
                    int(current_complexity.get("high_complexity_count", 0) or 0),
                    int(midpoint_complexity.get("high_complexity_count", 0) or 0),
                ),
            },
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
                self._git(repo_root, "checkout", "--detach", commit_point.hash)
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

    def _git(self, repo_root: Path, *args: str) -> str:
        cmd = ["git", "-C", str(repo_root), *args]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Git command failed: {' '.join(args)}. {proc.stderr.strip()}",
            )
        return proc.stdout

    @staticmethod
    def _count_delta(current_value: int, midpoint_value: int) -> dict:
        return {
            "current": current_value,
            "midpoint": midpoint_value,
            "delta": current_value - midpoint_value,
        }

    @staticmethod
    def _set_delta(current_values, midpoint_values) -> dict:
        current_set = {str(v) for v in (current_values or [])}
        midpoint_set = {str(v) for v in (midpoint_values or [])}
        return {
            "added": sorted(current_set - midpoint_set),
            "removed": sorted(midpoint_set - current_set),
        }
