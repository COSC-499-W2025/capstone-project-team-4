"""Tests for snapshot comparison functionality."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.orm import Project, Language, Framework, ProjectFramework, File


@pytest.fixture
def project1(test_db: Session) -> Project:
    """Create first test project (earlier snapshot)."""
    project = Project(
        name="Demo-Old",
        root_path="/tmp/demo-mid",
        source_type="github",
        source_url="https://github.com/test/demo",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        zip_uploaded_at=datetime.now(timezone.utc),
        first_file_created=datetime.now(timezone.utc),
        first_commit_date=datetime.now(timezone.utc),
        project_started_at=datetime.now(timezone.utc),
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)

    # Add languages via Files
    python = test_db.query(Language).filter_by(name="Python").first()
    if not python:
        python = Language(name="Python")
        test_db.add(python)
        test_db.commit()

    # Create files with Python language
    for i in range(5):
        file = File(
            project_id=project.id,
            path=f"src/file{i}.py",
            language_id=python.id,
            lines_of_code=100,
        )
        test_db.add(file)

    # Add frameworks
    flask = test_db.query(Framework).filter_by(name="Flask").first()
    if not flask:
        flask = Framework(name="Flask")
        test_db.add(flask)
        test_db.commit()

    proj_fw = ProjectFramework(project_id=project.id, framework_id=flask.id)
    test_db.add(proj_fw)

    test_db.commit()

    return project


@pytest.fixture
def project2(test_db: Session) -> Project:
    """Create second test project (later snapshot with more features)."""
    project = Project(
        name="Demo-Current",
        root_path="/tmp/demo-late",
        source_type="github",
        source_url="https://github.com/test/demo",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        zip_uploaded_at=datetime.now(timezone.utc),
        first_file_created=datetime.now(timezone.utc),
        first_commit_date=datetime.now(timezone.utc),
        project_started_at=datetime.now(timezone.utc),
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)

    # Add multiple languages (Python + JavaScript) via Files
    for lang_name, ext in [("Python", ".py"), ("JavaScript", ".js")]:
        language = test_db.query(Language).filter_by(name=lang_name).first()
        if not language:
            language = Language(name=lang_name)
            test_db.add(language)
            test_db.commit()

        # Create files with this language
        for i in range(5):
            file = File(
                project_id=project.id,
                path=f"src/file{i}{ext}",
                language_id=language.id,
                lines_of_code=100,
            )
            test_db.add(file)

    # Add multiple frameworks (Flask + React)
    for fw_name in ["Flask", "React"]:
        framework = test_db.query(Framework).filter_by(name=fw_name).first()
        if not framework:
            framework = Framework(name=fw_name)
            test_db.add(framework)
            test_db.commit()

        proj_fw = ProjectFramework(project_id=project.id, framework_id=framework.id)
        test_db.add(proj_fw)

    test_db.commit()

    return project


def test_compare_snapshots_by_id(
    client: TestClient,
    project1: Project,
    project2: Project,
):
    """Test comparing snapshots by project ID."""
    response = client.get(
        f"/api/snapshots/compare?project1_id={project1.id}&project2_id={project2.id}"
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["snapshot1_name"] == "Demo-Old"
    assert data["snapshot2_name"] == "Demo-Current"
    assert "summary" in data

    # Verify metric comparisons exist
    assert "contributors" in data
    assert "languages" in data
    assert "frameworks" in data
    assert "libraries" in data
    assert "total_files" in data
    assert "total_loc" in data

    # Verify new items detection
    assert "new_languages" in data
    assert "new_frameworks" in data
    assert "new_libraries" in data

    # Verify language progression
    assert "JavaScript" in data["new_languages"]
    assert len(data["languages"]["snapshot1_value"]) == 1
    assert len(data["languages"]["snapshot2_value"]) == 2

    # Verify framework progression
    assert "React" in data["new_frameworks"]
    assert len(data["frameworks"]["snapshot1_value"]) == 1
    assert len(data["frameworks"]["snapshot2_value"]) == 2


def test_compare_missing_project1_params(client: TestClient):
    """Test comparison fails when project1_id is missing."""
    response = client.get("/api/snapshots/compare?project2_id=1")

    assert response.status_code == 422  # Validation error
    assert "project1_id" in response.text.lower()


def test_compare_missing_project2_params(client: TestClient, project1: Project):
    """Test comparison fails when project2_id is missing."""
    response = client.get(f"/api/snapshots/compare?project1_id={project1.id}")

    assert response.status_code == 422  # Validation error
    assert "project2_id" in response.text.lower()


def test_compare_nonexistent_project1(client: TestClient, project2: Project):
    """Test comparison fails when project1 doesn't exist."""
    response = client.get(f"/api/snapshots/compare?project1_id=999&project2_id={project2.id}")

    assert response.status_code == 404
    assert "Project 1 not found" in response.json()["detail"]


def test_compare_nonexistent_project2(client: TestClient, project1: Project):
    """Test comparison fails when project2 doesn't exist."""
    response = client.get(f"/api/snapshots/compare?project1_id={project1.id}&project2_id=999")

    assert response.status_code == 404
    assert "Project 2 not found" in response.json()["detail"]


def test_metric_comparison_structure(
    client: TestClient,
    project1: Project,
    project2: Project,
):
    """Test that metric comparisons have correct structure."""
    response = client.get(
        f"/api/snapshots/compare?project1_id={project1.id}&project2_id={project2.id}"
    )

    assert response.status_code == 200
    data = response.json()

    # Check MetricComparison structure for languages
    lang_comparison = data["languages"]
    assert "snapshot1_value" in lang_comparison
    assert "snapshot2_value" in lang_comparison
    assert "change" in lang_comparison
    assert "percent_change" in lang_comparison

    # Verify change calculation (2 - 1 = 1 new language)
    assert lang_comparison["change"] == 1


def test_snapshot_metrics_structure(
    client: TestClient,
    project1: Project,
    project2: Project,
):
    """Test that snapshot metrics have correct structure."""
    response = client.get(
        f"/api/snapshots/compare?project1_id={project1.id}&project2_id={project2.id}"
    )

    assert response.status_code == 200
    data = response.json()

    # Verify snapshot1_metrics structure
    metrics1 = data["snapshot1_metrics"]
    assert metrics1["snapshot_name"] == "Demo-Old"
    assert "total_commits" in metrics1
    assert "contributor_count" in metrics1
    assert "languages" in metrics1
    assert "frameworks" in metrics1
    assert "libraries" in metrics1
    assert "tools" in metrics1
    assert "total_files" in metrics1
    assert "total_loc" in metrics1

    # Verify snapshot2_metrics structure
    metrics2 = data["snapshot2_metrics"]
    assert metrics2["snapshot_name"] == "Demo-Current"


def test_comparison_summary_generation(
    client: TestClient,
    project1: Project,
    project2: Project,
):
    """Test that comparison summary is generated correctly."""
    response = client.get(
        f"/api/snapshots/compare?project1_id={project1.id}&project2_id={project2.id}"
    )

    assert response.status_code == 200
    data = response.json()

    summary = data["summary"]
    assert isinstance(summary, str)
    assert len(summary) > 0

    # Summary should mention changes
    # With our test data: 1 new language, 1 new framework
    assert "language" in summary.lower() or "framework" in summary.lower()


def test_percent_change_calculation(
    client: TestClient,
    project1: Project,
    project2: Project,
):
    """Test that percent change is calculated correctly."""
    response = client.get(
        f"/api/snapshots/compare?project1_id={project1.id}&project2_id={project2.id}"
    )

    assert response.status_code == 200
    data = response.json()

    # Languages: 1 -> 2 = 100% increase
    lang_comparison = data["languages"]
    assert lang_comparison["percent_change"] == 100.0

    # Frameworks: 1 -> 2 = 100% increase
    fw_comparison = data["frameworks"]
    assert fw_comparison["percent_change"] == 100.0


def test_no_changes_comparison(
    client: TestClient,
    test_db: Session,
):
    """Test comparison when projects have identical metrics."""
    # Create two identical projects
    project_ids = []
    for name in ["Identical-1", "Identical-2"]:
        project = Project(
            name=name,
            root_path=f"/tmp/{name.lower()}",
            source_type="github",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            zip_uploaded_at=datetime.now(timezone.utc),
            first_file_created=datetime.now(timezone.utc),
            first_commit_date=datetime.now(timezone.utc),
            project_started_at=datetime.now(timezone.utc),
        )
        test_db.add(project)
        test_db.commit()
        test_db.refresh(project)
        project_ids.append(project.id)

        # Add same language via File
        python = test_db.query(Language).filter_by(name="Python").first()
        if not python:
            python = Language(name="Python")
            test_db.add(python)
            test_db.commit()

        # Create files with Python language
        for i in range(5):
            file = File(
                project_id=project.id,
                path=f"src/file{i}.py",
                language_id=python.id,
                lines_of_code=100,
            )
            test_db.add(file)
        test_db.commit()

    response = client.get(
        f"/api/snapshots/compare?project1_id={project_ids[0]}&project2_id={project_ids[1]}"
    )

    assert response.status_code == 200
    data = response.json()

    # No new items
    assert len(data["new_languages"]) == 0
    assert len(data["new_frameworks"]) == 0
    assert len(data["new_libraries"]) == 0

    # Changes should be 0
    assert data["languages"]["change"] == 0

    # Summary should indicate no changes
    assert "no significant changes" in data["summary"].lower()
