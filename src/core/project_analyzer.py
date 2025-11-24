import os
import json
from collections import defaultdict
from git import Repo, InvalidGitRepositoryError


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
        print(f"[WARN] No .git directory found at {project_path}. Returning empty contributors.")
        return []

    contributors = {}
    commit_counts = defaultdict(int)

    # NOTE: By default, it will get the commits from only the current branch HEAD. If you want to get all commits,
    # input -all instead. So it would be, `repo.iter_commits('--all')`

    commit_range = '--all' if use_all_branches else None
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
                "files_modified": defaultdict(int)
            }

        commit_counts[key] += 1

        stats = commit.stats

        # Per-file modifications
        for file_path, file_stats in stats.files.items():
            contributors[key]["files_modified"][file_path] += 1

        # Line-level stats
        contributors[key]["total_lines_added"] += stats.total.get("insertions", 0)
        contributors[key]["total_lines_deleted"] += stats.total.get("deletions", 0)

        # Commit history entry
        contributors[key]["history"].append({
            "hash": commit.hexsha,
            "message": commit.message.strip(),
            "timestamp": commit.committed_date,
            "files_changed": list(stats.files.keys()),
            "insertions": stats.total.get("insertions", 0),
            "deletions": stats.total.get("deletions", 0)
        })

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
    total_size = sum(f.get("file_size", 0) for f in file_list if f.get("file_size") is not None)
    avg_size = round(total_size / total_files, 2) if total_files > 0 else 0

    # Duration
    try:
        created_ts = min(f["created_timestamp"] for f in file_list if f["created_timestamp"] is not None)
        modified_ts = max(f["last_modified"] for f in file_list if f["last_modified"] is not None)
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
        "activity_types": "TODO idk someone can do that lol",
        "collaborative": is_collaborative,
        "contributors": contributors
    }

    return metrics


if __name__ == "__main__":
    # For local testing only
    print("[TEST] Running project analyzer...")

    cwd = os.getcwd()
    # By default, the metadata_parser puts the json as: capstone-project-team-4_metadata.json
    test_metadata_path = os.path.join(cwd, "src/outputs/capstone-project-team-4_metadata.json")

    with open(test_metadata_path, "r") as file:
        data = json.load(file)

    file_list = data["files"]
    # This is a fallback if it's missing
    project_path = data.get("project_root", cwd) 

    print(f"[INFO] Using project root: {project_path}")

    metrics = calculate_project_stats(project_path, file_list)

    print("\nPROJECT METRICS")
    print(json.dumps(metrics, indent=2))
