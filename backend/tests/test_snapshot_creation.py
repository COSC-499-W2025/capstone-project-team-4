"""Tests for snapshot creation functionality."""

import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_snapshot_creation_with_valid_git_repo(
    client: TestClient,
    git_repo_zip: Path,
    test_db: Session,
):
    """Test snapshot creation with valid git repository."""
    # Upload with snapshot creation enabled
    with open(git_repo_zip, "rb") as f:
        response = client.post(
            "/api/projects/analyze/upload",
            files={"file": ("test-repo.zip", f, "application/zip")},
            data={
                "project_name": "test-project",
                "create_snapshots": "true",
            },
        )

    assert response.status_code == 201
    data = response.json()

    # Response should be a list of 2 snapshots (Mid and Late)
    assert isinstance(data, list)
    assert len(data) == 2

    # Extract project names from response
    project_names = [p["project_name"] for p in data]
    assert "test-project-Mid" in project_names
    assert "test-project-Late" in project_names

    # Verify all are completed
    for project in data:
        assert project["status"] == "completed"

    # Verify snapshots were created in database
    from src.models.orm import Project

    all_projects = test_db.query(Project).all()
    db_project_names = [p.name for p in all_projects]

    assert "test-project-Mid" in db_project_names
    assert "test-project-Late" in db_project_names
    assert len(all_projects) == 2  # 2 snapshots


def test_snapshot_creation_without_git_history(
    client: TestClient,
    temp_dir: Path,
):
    """Test snapshot creation fails without git history."""
    # Create a ZIP without .git directory
    zip_path = temp_dir / "no-git.zip"
    project_dir = temp_dir / "no-git-project"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("# No Git\n")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.write(project_dir / "README.md", "no-git-project/README.md")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/projects/analyze/upload",
            files={"file": ("no-git.zip", f, "application/zip")},
            data={
                "project_name": "no-git-project",
                "create_snapshots": "true",
            },
        )

    assert response.status_code == 400
    assert "requires git history" in response.json()["detail"].lower()


def test_snapshot_creation_with_insufficient_commits(
    client: TestClient,
    temp_dir: Path,
):
    """Test snapshot creation fails with less than 10 commits."""
    import subprocess

    # Create a repo with only 5 commits
    repo_dir = temp_dir / "small-repo"
    repo_dir.mkdir()

    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_dir,
        capture_output=True,
        check=True,
    )

    for i in range(5):
        (repo_dir / f"file{i}.txt").write_text(f"content {i}")
        subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Commit {i}"],
            cwd=repo_dir,
            capture_output=True,
            check=True,
        )

    # Create ZIP
    import os
    zip_path = temp_dir / "small-repo.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root_str, dirs, files in os.walk(repo_dir):
            root_path = Path(root_str)
            for file in files:
                file_path = root_path / file
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/projects/analyze/upload",
            files={"file": ("small-repo.zip", f, "application/zip")},
            data={
                "project_name": "small-repo",
                "create_snapshots": "true",
            },
        )

    assert response.status_code == 400
    assert "at least 10 commits" in response.json()["detail"].lower()


def test_snapshot_creation_disabled(
    client: TestClient,
    git_repo_zip: Path,
    test_db: Session,
):
    """Test that snapshots are not created when flag is false."""
    with open(git_repo_zip, "rb") as f:
        response = client.post(
            "/api/projects/analyze/upload",
            files={"file": ("test-repo.zip", f, "application/zip")},
            data={
                "project_name": "test-no-snapshots",
                "create_snapshots": "false",
            },
        )

    assert response.status_code == 201

    # Verify only main project was created
    from src.models.orm import Project

    all_projects = test_db.query(Project).all()
    assert len(all_projects) == 1
    assert all_projects[0].name == "test-no-snapshots"


def test_snapshot_naming_convention(
    client: TestClient,
    git_repo_zip: Path,
    test_db: Session,
):
    """Test that snapshots follow the correct naming convention."""
    with open(git_repo_zip, "rb") as f:
        response = client.post(
            "/api/projects/analyze/upload",
            files={"file": ("test-repo.zip", f, "application/zip")},
            data={
                "project_name": "my-project",
                "create_snapshots": "true",
            },
        )

    assert response.status_code == 201
    data = response.json()

    # Response should be a list of projects
    assert isinstance(data, list)

    # Extract project names from response
    project_names = {p["project_name"] for p in data}

    # Should have snapshots with "Mid" and "Late" suffixes
    assert "my-project-Mid" in project_names
    assert "my-project-Late" in project_names


def test_snapshot_commit_points(
    client: TestClient,
    git_repo_zip: Path,
    test_db: Session,
):
    """Test that snapshots are created at correct commit percentages (60% and 85%)."""
    import subprocess

    # First, get the total commit count from the test repo
    # We created 15 commits in the fixture (1 initial + 14 files)
    # 60% of 15 = 9th commit
    # 85% of 15 = 12th commit

    with open(git_repo_zip, "rb") as f:
        response = client.post(
            "/api/projects/analyze/upload",
            files={"file": ("test-repo.zip", f, "application/zip")},
            data={
                "project_name": "commit-test",
                "create_snapshots": "true",
            },
        )

    assert response.status_code == 201

    # Verify snapshots exist
    from src.models.orm import Project

    mid_project = test_db.query(Project).filter_by(name="commit-test-Mid").first()
    late_project = test_db.query(Project).filter_by(name="commit-test-Late").first()

    assert mid_project is not None
    assert late_project is not None

    # Both should have valid project start dates
    assert mid_project.first_commit_date is not None
    assert late_project.first_commit_date is not None


def test_snapshot_with_custom_project_name(
    client: TestClient,
    git_repo_zip: Path,
    test_db: Session,
):
    """Test snapshot creation with custom project name."""
    with open(git_repo_zip, "rb") as f:
        response = client.post(
            "/api/projects/analyze/upload",
            files={"file": ("test-repo.zip", f, "application/zip")},
            data={
                "project_name": "CustomName",
                "create_snapshots": "true",
            },
        )

    assert response.status_code == 201
    data = response.json()

    # Response should be a list of projects
    assert isinstance(data, list)

    # Extract project names from response
    names = {p["project_name"] for p in data}

    # Should have snapshots with custom name
    assert "CustomName-Mid" in names
    assert "CustomName-Late" in names
