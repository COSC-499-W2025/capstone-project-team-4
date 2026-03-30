from __future__ import annotations

from contextlib import asynccontextmanager
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
    """TestClient with lifespan disabled and DB/auth dependencies overridden."""

    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = no_lifespan

    def _get_db_override():
        # Route only needs a dependency object; service is monkeypatched.
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


def _analysis_result_payload(project_id: int = 1):
    # Minimal payload satisfying response schema used by routes.
    return {
        "project_id": project_id,
        "project_name": "Demo Project",
        "status": "completed",
        "source_type": "zip",
        "zip_uploaded_at": "2024-01-01T00:00:00+00:00",
        "first_file_created": "2024-01-01T00:00:00+00:00",
        "project_started_at": "2024-01-01T00:00:00+00:00",
    }


def test_upload_endpoint_passes_reuse_cached_analysis_false(client, monkeypatch):
    captured = {}

    def fake_analyze_from_zip(self, zip_path, project_name, use_cache=True, **kwargs):
        if kwargs.get("reuse_cached_analysis") is not None:
            use_cache = kwargs["reuse_cached_analysis"]
        captured["use_cache"] = use_cache
        return [_analysis_result_payload(1)]

    monkeypatch.setattr(AnalysisService, "analyze_from_zip", fake_analyze_from_zip)

    response = client.post(
        "/api/projects/analyze/upload",
        data={"project_name": "Demo Project", "reuse_cached_analysis": "false"},
        files={"file": ("demo.zip", b"fake-zip", "application/zip")},
    )

    assert response.status_code == 201
    assert captured["use_cache"] is False


def test_upload_endpoint_passes_reuse_cached_analysis_true_by_default(
    client, monkeypatch
):
    captured = {}

    def fake_analyze_from_zip(self, zip_path, project_name, use_cache=True, **kwargs):
        if kwargs.get("reuse_cached_analysis") is not None:
            use_cache = kwargs["reuse_cached_analysis"]
        captured["use_cache"] = use_cache
        return [_analysis_result_payload(1)]

    monkeypatch.setattr(AnalysisService, "analyze_from_zip", fake_analyze_from_zip)

    response = client.post(
        "/api/projects/analyze/upload",
        data={"project_name": "Demo Project"},
        files={"file": ("demo.zip", b"fake-zip", "application/zip")},
    )

    assert response.status_code == 201
    assert captured["use_cache"] is True
