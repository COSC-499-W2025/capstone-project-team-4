from git import Repo
# Use defaultdict instead of a regular dict to initialize default keys automatically 
from collections import defaultdict

import os
import json

def analyze_contributors(project_path="."):
    """
    Analyze contributors using commit history.
    Groups contributors by NAME (to avoid duplicate emails).
    Also includes:
      - full commit history per contributor
      - lines added/removed
      - files changed
    """
    repo = Repo(project_path)

    # Main storage
    contributors = {}
    commit_counts = defaultdict(int)

    # Also, by default, iter_commits() will take the HEAD branch so... yeah keep that in mind
    for commit in repo.iter_commits():
        name = commit.author.name.strip()
        email = commit.author.email.lower().strip()

        # Skip GitHub bots
        if "[bot]" in name.lower():
            continue

        key = name.lower()

        # Initialize contributor entry if not exist
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

        # Count commit
        commit_counts[key] += 1

        # Extract commit stats
        stats = commit.stats

        # Track file modifications
        for file_path, file_stats in stats.files.items():
            contributors[key]["files_modified"][file_path] += 1

        # Track lines added/removed
        contributors[key]["total_lines_added"] += stats.total.get("insertions", 0)
        contributors[key]["total_lines_deleted"] += stats.total.get("deletions", 0)

        # Add entry to commit history
        contributors[key]["history"].append({
            # Yeah idk why it's called hexsha but eh
            "hash": commit.hexsha,
            "message": commit.message.strip(),
            "timestamp": commit.committed_date,
            "files_changed": list(stats.files.keys()),
            "insertions": stats.total.get("insertions", 0),
            "deletions": stats.total.get("deletions", 0)
        })

    # Calculate total commits
    total_commits = sum(commit_counts.values())

    # Final formatting
    contributor_list = []
    for key, data in contributors.items():
        commit_count = commit_counts[key]
        data["commits"] = commit_count
        data["percent"] = round((commit_count / total_commits) * 100, 2)

        # Convert defaultdict to regular dict for JSON
        data["files_modified"] = dict(data["files_modified"])

        contributor_list.append(data)

    return contributor_list


def calculate_project_stats(project_name, file_list):
    """
    Calculates the metrics for a given project.
    This includes file stats, duration, and the contributor info

    Args:
        project_name (str):  The name of the directory itself. This helps in finding if a `.git` file is found.
        file_list (list[files]): From A1's task, this should be a list of files. A1 should have utilized the `metadata.json`
                                 and return a proper list of files
    """

    # File stats
    total_files = len(file_list)
    total_size = sum(file["file_size"] for file in file_list)
    avg_size = round(total_size / total_size, 2) if total_files > 0 else 0

    # Duration (in days, idk if we should use different measures of time but oh well)
    seconds_in_day = 86_400
    created = min(file["created_timestamp"] for file in file_list)
    modified = max(file["last_modified"] for file in file_list)
    # It's 86400 because there's 86400
    duration_days = round((modified - created) / seconds_in_day, 2)

    # Activity type (like the language, skills used, etc. idk man idk)
    # TODO: The activity type, idk lol
    # Since A3 is working on that, just uh.. yeah I'll leave it blank for now

    # Contributors
    project_path = os.path.join(os.getcwd(), project_name)
    contributors = []
    if os.path.exists(os.path.join(project_path, ".git")):
        contributors = analyze_contributors(project_path)
    else :
        # Yeah I think it makes sense if we literally just make contributors to be None
        contributors = None
    
    # Find if it's a solo or collaborative
    is_collaborative = True if not contributors is None else False

    metrics = {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "average_file_size_bytes": avg_size,
        "duration_days": duration_days,
        "activity_types": "Uh.. chicken! It's not done yet!",
        "collaborative": is_collaborative,
        "contributors": contributors
    }

    return metrics
if __name__ == "__main__":
    # For testing, just use the current working directory
    working_directory = os.getcwd()
    outputs_directory = os.path.join(working_directory, "src/outputs")
    metadata_path = os.path.join(outputs_directory, "test_metadata.json")
    contributors = analyze_contributors(working_directory);

    # For testing, get the metadata.json thing from the first part
    # print(outputs_directory)


    """
    TODO:Maybe... the metadata.json file should have the project root? Just so it can find the .git file
     Right now, test_metadata.json just has `files` (list) and `metadata` so maybe there should be another one called
     project_root?
    """
    with open(metadata_path, "r") as file:
        data = json.load(file)
        files = data["files"]
        project_name = r"outputs"
        metrics = calculate_project_stats(project_name, files)
        print()
        print(f"Metrics: {metrics}")

    filename = "src/outputs/contributor.json"

    # Open the file in write mode ('w') and use json.dump() to write the data
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(contributors[0], json_file, indent=4)