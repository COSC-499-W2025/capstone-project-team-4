import os
import subprocess
from src.core.analyzer.project_analyzer import calculate_project_stats, analyze_contributors

def test_calculate_project_stats():
    file_list = [
        {"file_size": 100, "created_timestamp": 10, "last_modified": 20},
        {"file_size": 300, "created_timestamp": 5, "last_modified": 25},
    ]

    # dummy project root
    project_root = os.getcwd()

    metrics = calculate_project_stats(project_root, file_list)

    assert metrics["total_files"] == 2
    assert metrics["total_size_bytes"] == 400
    assert metrics["average_file_size_bytes"] == 200
    assert metrics["duration_days"] == round((25 - 5) / 86400, 2)

def test_analyze_contributors_with_dummy_repo(tmp_path):
    # Create a temporary Git repo
    repo_path = tmp_path / "repo"
    os.makedirs(repo_path, exist_ok=True)

    # Initialize Git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True)

    # Create a file and commit
    file_path = repo_path / "test.txt"
    with open(file_path, "w") as f:
        f.write("hello")

    subprocess.run(["git", "add", "test.txt"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Tester", "-c", "user.email=test@example.com", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True
    )

    # Analyze the repo
    contributors = analyze_contributors(str(repo_path))

    assert len(contributors) == 1
    assert contributors[0]["name"] == "Tester"
    assert contributors[0]["commits"] == 1

def test_analyze_contributors_no_git(tmp_path):
    contributors = analyze_contributors(str(tmp_path))
    assert contributors == []
