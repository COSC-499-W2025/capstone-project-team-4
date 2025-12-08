from __future__ import annotations
import os
import json
from collections import defaultdict
from git import Repo, InvalidGitRepositoryError
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List
from src.core.code_complexity import (
    FunctionMetrics,
    analyze_file,
    EXT_TO_LANG,
)


# Git/Collaboration Analysis Functions
def analyze_contributors(project_path=".", use_all_branches=False):
    """
    Analyze commit history for all contributors.
    Groups by contributor NAME to avoid duplicates (noreply vs real email).
    If use_all_branches=True then use '--all', otherwise just analyze the current branch

    Includes:
        - total commits
        - percent of total commits
        - commit history
        - lines added / deleted
        - files modified
    """

    try:
        repo = Repo(project_path)
    except InvalidGitRepositoryError:
        print(
            f"[WARN] No .git directory found at {project_path}. Returning empty contributors."
        )
        return []

    contributors = {}
    commit_counts = defaultdict(int)

    # NOTE: By default, it will get the commits from only the current branch HEAD. If you want to get all commits,
    # input -all instead. So it would be, `repo.iter_commits('--all')`

    commit_range = "--all" if use_all_branches else None
    for commit in repo.iter_commits(commit_range):
        name = commit.author.name.strip()
        email = commit.author.email.strip().lower()

    try:
        commit_range = "--all" if use_all_branches else None
        for commit in repo.iter_commits(commit_range):
            name = commit.author.name.strip()
            email = commit.author.email.strip().lower()

            # Skip bots
            if "[bot]" in name.lower():
                continue

            key = name.lower()  # unify identity by name

            # Initialize contributor record
            if key not in contributors:
                contributors[key] = {
                    "name": name,
                    "primary_email": email,
                    "commits": 0,
                    "percent": 0,
                    "history": [],
                    "total_lines_added": 0,
                    "total_lines_deleted": 0,
                    "files_modified": defaultdict(int),
                }

            commit_counts[key] += 1

            try:
                stats = commit.stats
                # Per-file modifications
                for file_path, file_stats in stats.files.items():
                    contributors[key]["files_modified"][file_path] += 1

                # Line-level stats
                contributors[key]["total_lines_added"] += stats.total.get(
                    "insertions", 0
                )
                contributors[key]["total_lines_deleted"] += stats.total.get(
                    "deletions", 0
                )

                # Commit history entry
                contributors[key]["history"].append(
                    {
                        "hash": commit.hexsha,
                        "message": commit.message.strip(),
                        "timestamp": commit.committed_date,
                        "files_changed": list(stats.files.keys()),
                        "insertions": stats.total.get("insertions", 0),
                        "deletions": stats.total.get("deletions", 0),
                    }
                )
            except Exception as stats_error:
                print(
                    f"[WARN] Error getting stats for commit {commit.hexsha}: {stats_error}"
                )
                # Add commit without stats
                contributors[key]["history"].append(
                    {
                        "hash": commit.hexsha,
                        "message": commit.message.strip(),
                        "timestamp": commit.committed_date,
                        "files_changed": [],
                        "insertions": 0,
                        "deletions": 0,
                    }
                )

    except Exception as e:
        print(
            f"[WARN] Error accessing Git repository commits: {e}. Returning empty contributors."
        )
        return []

    # Format contributors into final list
    total_commits = sum(commit_counts.values())
    contributor_list = []

    for key, info in contributors.items():
        commit_count = commit_counts[key]
        info["commits"] = commit_count

        if total_commits > 0:
            info["percent"] = round((commit_count / total_commits) * 100, 2)
        else:
            info["percent"] = 0

        # Convert defaultdict to normal dict for JSON
        info["files_modified"] = dict(info["files_modified"])

        contributor_list.append(info)

    return contributor_list


def calculate_project_stats(project_path, file_list):
    """
    Given the project root (with .git) and the file metadata list,
    compute full project-level statistics.
    """

    # File Stats
    total_files = len(file_list)
    total_size = sum(
        f.get("file_size", 0) for f in file_list if f.get("file_size") is not None
    )
    avg_size = round(total_size / total_files, 2) if total_files > 0 else 0

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

    # Contributors
    # For this, we can just analyze the current branch. Set `use_all_branches=True` if all branches need the commit history
    contributors = analyze_contributors(project_path)
    is_collaborative = len(contributors) > 1

    # Final Metrics
    metrics = {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "average_file_size_bytes": avg_size,
        "duration_days": duration_days,
        "collaborative": is_collaborative,
    }

    return metrics


def save_project_metrics(metrics: dict, output_filename="project_metrics.json"):
    """
    Save project metrics (from calculate_project_stats) to JSON inside src/outputs
    """

    outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    output_path = os.path.join(outputs_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Project metrics saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # For local testing only
    print("[TEST] Running project analyzer...")

    cwd = os.getcwd()
    # By default, the metadata_parser puts the json as: capstone-project-team-4_metadata.json
    test_metadata_path = os.path.join(
        cwd, "src/outputs/capstone-project-team-4_metadata.json"
    )

    with open(test_metadata_path, "r") as file:
        data = json.load(file)

    file_list = data["files"]
    # This is a fallback if it's missing
    project_path = data.get("project_root", cwd)

    print(f"[INFO] Using project root: {project_path}")

    metrics = calculate_project_stats(project_path, file_list)

    # NOTE: I removed the print statements as now you can just read the generated json file.
    # It clutters the terminal so yeah
    # print("\nPROJECT METRICS")
    # print(json.dumps(metrics, indent=2))

    save_project_metrics(metrics)


# Tree-sitter Analysis Integration
@dataclass
class ProjectAnalysisResult:
    project_root: str
    functions: List[FunctionMetrics]


def _is_ignored(path: Path) -> bool:
    ignored = {".venv", "venv", "__pycache__", ".git", ".pytest_cache"}
    return any(part in ignored for part in path.parts)


def _should_analyze(path: Path) -> bool:
    if not path.is_file():
        return False
    if _is_ignored(path):
        return False
    if path.suffix.lower() not in EXT_TO_LANG:
        return False
    return True


def analyze_project(root: Path) -> ProjectAnalysisResult:
    root = root.resolve()
    functions: List[FunctionMetrics] = []

    if root.is_file():
        if _should_analyze(root):
            functions.extend(analyze_file(root))
    else:
        for path in root.rglob("*"):
            if _should_analyze(path):
                functions.extend(analyze_file(path))

    return ProjectAnalysisResult(
        project_root=str(root),
        functions=functions,
    )


def project_analysis_to_dict(result: ProjectAnalysisResult) -> dict:
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
