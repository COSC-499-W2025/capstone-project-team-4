from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import get_current_user
from src.models.database import get_db
from src.services.analysis_service import AnalysisService


@pytest.fixture()
def client() -> Iterator[TestClient]:
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = no_lifespan

    def _get_db_override():
        yield SimpleNamespace()

    fake_user = SimpleNamespace(id=1, email="test@example.com", is_active=True)

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.router.lifespan_context = original_lifespan


def _now() -> datetime:
    return datetime(2024, 1, 1, tzinfo=timezone.utc)


def _analysis_result_payload():
    # Minimal payload that satisfies the response schema.
    now = _now().isoformat()
    return {
        "project_id": 1,
        "project_name": "Demo Project",
        "status": "completed",
        "source_type": "local",
        "zip_uploaded_at": now,
        "first_file_created": now,
        "project_started_at": now,
    }


def test_analyze_upload_invalid_extension(client):
    # Verify invalid extensions are rejected before analysis runs.
    response = client.post(
        "/api/projects/analyze/upload",
        files={"file": ("demo.txt", b"not-zip", "text/plain")},
    )

    assert response.status_code == 400


def test_analyze_upload_status_and_data(client, monkeypatch):
    # Stub analysis so we only validate HTTP status and response shape.
    monkeypatch.setattr(
        AnalysisService,
        "analyze_from_zip",
        lambda *_args, **_kwargs: [_analysis_result_payload()],
    )

    response = client.post(
        "/api/projects/analyze/upload",
        data={"project_name": "Demo Project"},
        files={"file": ("demo.zip", b"fake-zip", "application/zip")},
    )

    assert response.status_code == 201
    assert response.json()[0]["project_id"] == 1
