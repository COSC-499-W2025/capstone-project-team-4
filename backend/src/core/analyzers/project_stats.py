"""
Project statistics and complexity analysis module.

This module provides project-level statistics calculation and
code complexity analysis across the entire project.

Migrated from src/core/project_analyzer.py
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Any

from src.core.analyzers.complexity import FunctionMetrics, analyze_file, EXT_TO_LANG
from src.core.analyzers.contributor import analyze_contributors
from src.core.constants import SKIP_DIRECTORIES

logger = logging.getLogger(__name__)


# =============================================================================
# Data classes
# =============================================================================


@dataclass
class ProjectAnalysisResult:
    """Result of project complexity analysis."""

    project_root: str
    functions: List[FunctionMetrics]


# =============================================================================
# Helper functions
# =============================================================================


def _is_ignored(path: Path, root: Path = None) -> bool:
    """Check if a path should be ignored during analysis.

    Args:
        path: Path to check
        root: Optional root path for relative checking (avoids /tmp false positives on Linux)
    """
    if root:
        try:
            relative_path = path.relative_to(root)
            return any(part in SKIP_DIRECTORIES for part in relative_path.parts)
        except ValueError:
            pass

    # Fallback: only check directory names, excluding system paths
    SYSTEM_DIRS = {"/", "tmp", "temp", "var", "home", "Users", "app"}
    return any(
        part in SKIP_DIRECTORIES and part not in SYSTEM_DIRS for part in path.parts
    )


def _should_analyze(path: Path, root: Path = None) -> bool:
    """Check if a file should be analyzed for complexity.

    Args:
        path: Path to the file
        root: Optional root path for relative checking
    """
    if not path.is_file():
        return False
    if _is_ignored(path, root):
        return False
    if path.suffix.lower() not in EXT_TO_LANG:
        return False
    return True


# =============================================================================
# Project statistics
# =============================================================================


def calculate_project_stats(
    project_path: str,
    file_list: List[Dict[str, Any]],
    contributors: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Given the project root (with .git) and the file metadata list,
    compute full project-level statistics.

    Args:
        project_path: Path to the project root
        file_list: List of file metadata dictionaries
        contributors: Optional pre-analyzed contributors list.
                     If None, will analyze contributors (slower).

    Returns:
        Dictionary containing project metrics
    """
    # File Stats
    total_files = len(file_list)
    total_size = sum(
        f.get("file_size", 0) for f in file_list if f.get("file_size") is not None
    )
    avg_size = round(total_size / total_files, 2) if total_files > 0 else 0

    # Calculate total lines of code
    total_lines = sum(
        f.get("lines_of_code", 0)
        for f in file_list
        if f.get("lines_of_code") is not None
    )

    # Duration
    try:
        created_ts = min(
            f["created_timestamp"]
            for f in file_list
            if f["created_timestamp"] is not None
        )
        modified_ts = max(
            f["last_modified"] for f in file_list if f["last_modified"] is not None
        )
        duration_days = round((modified_ts - created_ts) / 86400, 2)
    except ValueError:
        duration_days = 0

    # Contributors - use provided list or analyze
    if contributors is None:
        logger.info("Analyzing contributors for project stats...")
        try:
            contributors = analyze_contributors(project_path, use_all_branches=False)
            logger.info(f"Found {len(contributors)} contributors")
        except Exception as e:
            logger.warning(f"Contributor analysis failed: {e}")
            contributors = []

    contributor_count = len(contributors)
    is_collaborative = contributor_count > 1

    # Final Metrics
    metrics = {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "average_file_size_bytes": avg_size,
        "total_lines": total_lines,
        "duration_days": duration_days,
        "collaborative": is_collaborative,
        "contributor_count": contributor_count,
    }

    return metrics


def save_project_metrics(
    metrics: Dict[str, Any], output_filename: str = "project_metrics.json"
) -> str:
    """
    Save project metrics to JSON inside outputs directory.

    Args:
        metrics: Project metrics dictionary
        output_filename: Name of the output file

    Returns:
        Path to the saved file
    """
    outputs_dir = Path.cwd() / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    output_path = outputs_dir / output_filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    logger.info("Project metrics saved to: %s", output_path)
    return str(output_path)


# =============================================================================
# Complexity analysis
# =============================================================================


def analyze_project(
    root: Path,
    file_paths: List[Path] = None,
) -> ProjectAnalysisResult:
    """
    Analyze a project for function complexity metrics.

    Args:
        root: Path to the project root or single file
        file_paths: Optional pre-collected list of file paths to analyze.
                   If provided, skips file system traversal.

    Returns:
        ProjectAnalysisResult containing all function metrics
    """
    root = root.resolve()
    functions: List[FunctionMetrics] = []

    if root.is_file():
        if _should_analyze(root, root.parent):
            functions.extend(analyze_file(root))
    elif file_paths is not None:
        # Use pre-collected file paths (avoids redundant rglob)
        for path in file_paths:
            if _should_analyze(path, root):
                functions.extend(analyze_file(path))
    else:
        # Fall back to traversing file system
        for path in root.rglob("*"):
            if _should_analyze(path, root):
                functions.extend(analyze_file(path))

    return ProjectAnalysisResult(
        project_root=str(root),
        functions=functions,
    )


def project_analysis_to_dict(result: ProjectAnalysisResult) -> Dict[str, Any]:
    """
    Convert ProjectAnalysisResult to a dictionary with summary statistics.

    Args:
        result: ProjectAnalysisResult from analyze_project

    Returns:
        Dictionary with summary, per-file stats, and function details
    """
    funcs = result.functions

    total_functions = len(funcs)
    total_complexity = sum(f.cyclomatic_complexity for f in funcs)
    total_lines = sum(f.length_lines for f in funcs)

    avg_complexity = total_complexity / total_functions if total_functions else 0.0
    avg_lines = total_lines / total_functions if total_functions else 0.0
    avg_complexity_per_10 = (
        sum(f.complexity_per_10_lines for f in funcs) / total_functions
        if total_functions
        else 0.0
    )
    max_complexity = max((f.cyclomatic_complexity for f in funcs), default=0)
    max_loop_depth = max((f.max_loop_depth for f in funcs), default=0)

    # Complexity buckets
    buckets = {
        "1-5": 0,
        "6-10": 0,
        "11-20": 0,
        "21+": 0,
    }
    for f in funcs:
        c = f.cyclomatic_complexity
        if c <= 5:
            buckets["1-5"] += 1
        elif c <= 10:
            buckets["6-10"] += 1
        elif c <= 20:
            buckets["11-20"] += 1
        else:
            buckets["21+"] += 1

    # Per-file statistics
    per_file: Dict[str, dict] = {}
    for f in funcs:
        pf = per_file.setdefault(
            f.file_path,
            {
                "function_count": 0,
                "total_complexity": 0,
                "max_complexity": 0,
                "total_lines": 0,
            },
        )
        pf["function_count"] += 1
        pf["total_complexity"] += f.cyclomatic_complexity
        pf["total_lines"] += f.length_lines
        pf["max_complexity"] = max(pf["max_complexity"], f.cyclomatic_complexity)

    for path, stats in per_file.items():
        n = stats["function_count"]
        stats["avg_complexity"] = round(stats["total_complexity"] / n, 2)
        stats["avg_lines"] = round(stats["total_lines"] / n, 2)

    return {
        "project_root": result.project_root,
        "summary": {
            "total_functions": total_functions,
            "total_lines": total_lines,
            "avg_cyclomatic_complexity": round(avg_complexity, 2),
            "avg_lines_per_function": round(avg_lines, 2),
            "avg_complexity_per_10_lines": round(avg_complexity_per_10, 2),
            "max_complexity": max_complexity,
            "complexity_buckets": buckets,
            "max_loop_depth": max_loop_depth,
        },
        "per_file": per_file,
        "functions": [asdict(f) for f in funcs],
    }
