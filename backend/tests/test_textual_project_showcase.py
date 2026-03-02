from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.models.schemas.analysis import (
    TextualProjectShowcaseResponse,
    AnalysisStatus,
    ComplexitySummary,
)

# --- Minimal "service" interface we need for the route ---
class _FakeProjectService:
    def __init__(self) -> None:
        # defaults overridden per test by monkeypatching attrs
        self._exists = True
        self._result: Optional[TextualProjectShowcaseResponse] = None

    def project_exists(self, project_id: int) -> bool:
        return self._exists

    def get_textual_project_showcase(
        self, project_id: int
    ) -> Optional[TextualProjectShowcaseResponse]:
        return self._result


@pytest.fixture()
def app_and_service():
    """
    Build a tiny FastAPI app that reproduces ONLY the new endpoint behavior:
    - checks project_exists
    - raises 404 if missing
    - returns 404 if showcase missing
    - otherwise returns TextualProjectShowcaseResponse
    """
    app = FastAPI()
    service = _FakeProjectService()

    def get_service() -> _FakeProjectService:
        return service

    @app.get(
        "/projects/{project_id}/textual-project-showcase",
        response_model=TextualProjectShowcaseResponse,
    )
    async def get_textual_project_showcase(
        project_id: int,
        svc: _FakeProjectService = Depends(get_service),
    ):
        if not svc.project_exists(project_id):
            # mimic your consistent not-found outcome (status code matters most)
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        result = svc.get_textual_project_showcase(project_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Analysis data not available for this project.",
            )
        return result

    return app, service


@pytest.fixture()
def client(app_and_service):
    app, _ = app_and_service
    return TestClient(app)


def _sample_showcase(project_id: int = 123) -> TextualProjectShowcaseResponse:
    now = datetime.now(timezone.utc)
    return TextualProjectShowcaseResponse(
        project_id=project_id,
        project_name="Sample Project",
        status=AnalysisStatus.COMPLETED,
        short_description=None,
        source_type="upload",
        source_url=None,
        created_at=now,
        updated_at=now,
        languages=["Python"],
        frameworks=[],
        libraries=[],
        tools_and_technologies=[],
        contextual_skills=[],
        file_count=10,
        contributor_count=2,
        skill_count=5,
        library_count=0,
        tool_count=0,
        total_lines_of_code=200,
        complexity_summary=ComplexitySummary(
            total_functions=3,
            avg_complexity=2.0,
            max_complexity=4,
            high_complexity_count=0,
        ),
        zip_uploaded_at=now,
        first_file_created=now,
        first_commit_date=None,
        project_started_at=now,
        error_message=None,
    )


def test_showcase_200(client, app_and_service):
    _, service = app_and_service
    service._exists = True
    service._result = _sample_showcase(123)

    resp = client.get("/projects/123/textual-project-showcase")
    assert resp.status_code == 200

    data = resp.json()
    assert data["project_id"] == 123
    assert data["project_name"] == "Sample Project"
    assert data["status"] == "completed"
    assert data["short_description"] is None
    assert "created_at" in data and "updated_at" in data


def test_showcase_404_project_missing(client, app_and_service):
    _, service = app_and_service
    service._exists = False

    resp = client.get("/projects/999/textual-project-showcase")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_showcase_404_analysis_missing(client, app_and_service):
    _, service = app_and_service
    service._exists = True
    service._result = None

    resp = client.get("/projects/123/textual-project-showcase")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Analysis data not available for this project."