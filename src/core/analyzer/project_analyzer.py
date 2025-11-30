from __future__ import annotations
import os
import json
from collections import defaultdict
from git import Repo, InvalidGitRepositoryError
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List
from .code_complexity_analyzer import (
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
    print(f"📊 Starting contributor analysis for: {project_path}")
    print(f"🌳 Branch scope: {'All branches' if use_all_branches else 'Current branch only'}")

    try:
        repo = Repo(project_path)
        print(f"✅ Git repository found and loaded")
    except InvalidGitRepositoryError:
        print(
            f"❌ [WARN] No .git directory found at {project_path}. Returning empty contributors."
        )
        return []

    contributors = {}
    commit_counts = defaultdict(int)
    total_commits_processed = 0
    bots_skipped = 0

    # NOTE: By default, it will get the commits from only the current branch HEAD. If you want to get all commits,
    # input -all instead. So it would be, `repo.iter_commits('--all')`
    print(f"🔍 Starting commit history analysis...")

    commit_range = "--all" if use_all_branches else None

    try:
        commit_range = "--all" if use_all_branches else None
        for commit in repo.iter_commits(commit_range):
            total_commits_processed += 1
            name = commit.author.name.strip()
            email = commit.author.email.strip().lower()

            # Progress reporting every 50 commits
            if total_commits_processed % 50 == 0:
                print(f"  📊 Processed {total_commits_processed} commits, found {len(contributors)} unique contributors")

            # Skip bots
            if "[bot]" in name.lower():
                bots_skipped += 1
                continue

            key = name.lower()  # unify identity by name

            # Initialize contributor record
            if key not in contributors:
                print(f"  👤 New contributor discovered: {name} ({email})")
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
            f"❌ [WARN] Error accessing Git repository commits: {e}. Returning empty contributors."
        )
        return []

    print(f"✅ Commit analysis complete:")
    print(f"  📊 Total commits processed: {total_commits_processed}")
    print(f"  🤖 Bot commits skipped: {bots_skipped}")
    print(f"  👥 Unique contributors found: {len(contributors)}")

    # Format contributors into final list
    total_commits = sum(commit_counts.values())
    contributor_list = []
    print(f"\n🗜 Processing final contributor statistics...")

    for key, info in contributors.items():
        commit_count = commit_counts[key]
        info["commits"] = commit_count

        if total_commits > 0:
            info["percent"] = round((commit_count / total_commits) * 100, 2)
        else:
            info["percent"] = 0

        # Convert defaultdict to normal dict for JSON
        files_touched = len(info["files_modified"])
        info["files_modified"] = dict(info["files_modified"])
        
        print(f"  👤 {info['name']}: {commit_count} commits ({info['percent']}%), {files_touched} files touched")
        print(f"    ➕ Lines: +{info['total_lines_added']} / -{info['total_lines_deleted']}")

        contributor_list.append(info)

    print(f"✅ Contributor analysis complete: {len(contributor_list)} contributors processed\n")
    return contributor_list


def calculate_project_stats(project_path, file_list):
    """
    Given the project root (with .git) and the file metadata list,
    compute full project-level statistics.
    """
    print(f"📈 Calculating comprehensive project statistics...")
    print(f"📂 Project path: {project_path}")
    print(f"📊 File list contains: {len(file_list)} files")

    # File Stats
    print(f"  🗋 Computing file statistics...")
    total_files = len(file_list)
    total_size = sum(
        f.get("file_size", 0) for f in file_list if f.get("file_size") is not None
    )
    avg_size = round(total_size / total_files, 2) if total_files > 0 else 0
    print(f"    • Total files: {total_files}")
    print(f"    • Total size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print(f"    • Average file size: {avg_size:,} bytes")

    # Duration
    print(f"  🕒 Computing project duration...")
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
        print(f"    • Project duration: {duration_days} days")
        print(f"    • First file: {created_ts} | Latest: {modified_ts}")
    except ValueError:
        duration_days = 0
        print(f"    ⚠️  Unable to calculate duration (missing timestamps)")

    # Contributors
    # For this, we can just analyze the current branch. Set `use_all_branches=True` if all branches need the commit history
    print(f"\n👥 Analyzing project collaboration...")
    contributors = analyze_contributors(project_path)
    is_collaborative = len(contributors) > 1
    print(f"  🤝 Collaborative project: {'Yes' if is_collaborative else 'No'} ({len(contributors)} contributors)")

    # Final Metrics
    metrics = {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "average_file_size_bytes": avg_size,
        "duration_days": duration_days,
        "collaborative": is_collaborative,
    }

    print(f"\n✅ Project statistics calculation complete!")
    print(f"  🗊 Summary: {total_files} files, {duration_days} days, {len(contributors)} contributors\n")
    
    return metrics


def save_project_metrics(metrics: dict, output_filename="project_metrics.json"):
    """
    Save project metrics (from calculate_project_stats) to JSON in root /outputs
    """

    # Navigate to project root and use /outputs directory
    project_root = Path(__file__).resolve().parents[3]  # src/core/analyzer → src/core → src → root
    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    output_path = str(outputs_dir / output_filename)

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
        cwd, "outputs/capstone-project-team-4_metadata.json"
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
    print(f"📊 Starting project code complexity analysis...")
    print(f"📂 Target directory: {root}")
    
    root = root.resolve()
    functions: List[FunctionMetrics] = []
    files_processed = 0
    files_skipped = 0

    if root.is_file():
        print(f"📄 Analyzing single file: {root.name}")
        if _should_analyze(root):
            file_functions = analyze_file(root)
            functions.extend(file_functions)
            files_processed += 1
            print(f"  ✅ Found {len(file_functions)} functions")
        else:
            files_skipped += 1
            print(f"  ⚠️  File skipped (not supported or ignored)")
    else:
        print(f"📁 Analyzing directory recursively...")
        for path in root.rglob("*"):
            if _should_analyze(path):
                try:
                    file_functions = analyze_file(path)
                    functions.extend(file_functions)
                    files_processed += 1
                    
                    # Progress reporting every 10 files
                    if files_processed % 10 == 0:
                        print(f"  📊 Processed {files_processed} files, found {len(functions)} functions")
                        
                except Exception as e:
                    print(f"  ❌ Error analyzing {path}: {e}")
                    files_skipped += 1
            else:
                files_skipped += 1

    print(f"\n✅ Code complexity analysis complete!")
    print(f"  📄 Files processed: {files_processed}")
    print(f"  ⚠️  Files skipped: {files_skipped}")
    print(f"  🎯 Total functions found: {len(functions)}")
    if functions:
        avg_complexity = sum(f.cyclomatic_complexity for f in functions) / len(functions)
        max_complexity = max(f.cyclomatic_complexity for f in functions)
        print(f"  📈 Average complexity: {avg_complexity:.2f}")
        print(f"  🔥 Maximum complexity: {max_complexity}")
    print(f"")

    return ProjectAnalysisResult(
        project_root=str(root),
        functions=functions,
    )


def project_analysis_to_dict(result: ProjectAnalysisResult) -> dict:
    print(f"🗜 Processing complexity analysis results into structured format...")
    funcs = result.functions
    print(f"  🎯 Processing {len(funcs)} functions from: {result.project_root}")

    total_functions = len(funcs)
    total_complexity = sum(f.cyclomatic_complexity for f in funcs)
    total_lines = sum(f.length_lines for f in funcs)
    
    print(f"  📈 Computing aggregate statistics...")
    print(f"    • Total functions: {total_functions}")
    print(f"    • Total complexity: {total_complexity}")
    print(f"    • Total lines: {total_lines}")

    avg_complexity = total_complexity / total_functions if total_functions else 0.0
    avg_lines = total_lines / total_functions if total_functions else 0.0
    avg_complexity_per_10 = (
        sum(f.complexity_per_10_lines for f in funcs) / total_functions
        if total_functions
        else 0.0
    )
    max_complexity = max((f.cyclomatic_complexity for f in funcs), default=0)
    max_loop_depth = max((f.max_loop_depth for f in funcs), default=0)

    print(f"  🗺 Categorizing functions by complexity levels...")
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
    
    print(f"    • Complexity distribution: {buckets}")

    print(f"  📁 Computing per-file statistics...")
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
    
    print(f"    • Analyzed {len(per_file)} files with functions")

    for path, stats in per_file.items():
        n = stats["function_count"]
        stats["avg_complexity"] = round(stats["total_complexity"] / n, 2)
        stats["avg_lines"] = round(stats["total_lines"] / n, 2)

    result_dict = {
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
    
    print(f"\n✅ Complexity analysis data structure complete!")
    print(f"  📋 Generated summary with {len(result_dict['functions'])} function records")
    print(f"  📁 Per-file analysis for {len(per_file)} files")
    print(f"  📈 Overall average complexity: {round(avg_complexity, 2)}\n")
    
    return result_dict
