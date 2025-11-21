# src/core/project_analyzer.py

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

from src.core.code_complexity import analyze_python_file, FunctionMetrics


@dataclass
class ProjectAnalysisResult:
    project_root: str
    functions: List[FunctionMetrics]


def _is_ignored(path: Path) -> bool:
    """Skip venvs, caches, git, etc."""
    ignored = {".venv", "venv", "__pycache__", ".git", ".pytest_cache"}
    return any(part in ignored for part in path.parts)


def analyze_project(root: Path) -> ProjectAnalysisResult:
    """
    Walk a project folder OR analyze a single file;
    run Tree-sitter analysis on Python files and collect function-level metrics.
    """
    root = root.resolve()
    functions: List[FunctionMetrics] = []

    if root.is_file():
        # Single-file analysis
        if root.suffix == ".py" and not _is_ignored(root):
            functions.extend(analyze_python_file(root))
    else:
        # Directory: recurse through .py files
        for path in root.rglob("*.py"):
            if _is_ignored(path):
                continue
            functions.extend(analyze_python_file(path))

    return ProjectAnalysisResult(
        project_root=str(root),
        functions=functions,
    )


def project_analysis_to_dict(result: ProjectAnalysisResult) -> Dict:
    """Convert the dataclass result into something JSON-friendly."""
    return {
        "project_root": result.project_root,
        "functions": [asdict(f) for f in result.functions],
    }
