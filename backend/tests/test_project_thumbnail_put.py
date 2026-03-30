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
from src.services.project_service import ProjectService


@pytest.fixture()
def client() -> Iterator[TestClient]:
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = no_lifespan

    def _get_db_override():
        yield SimpleNamespace()

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, is_active=True)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.router.lifespan_context = original_lifespan


def test_put_thumbnail_unsupported_type(client, monkeypatch):
    monkeypatch.setattr(ProjectService, "user_owns_project", lambda *_: True)
    monkeypatch.setattr(ProjectService, "project_exists", lambda *_: True)

    resp = client.put(
        "/api/projects/1/thumbnail",
        files={"file": ("x.gif", b"gif", "image/gif")},
    )
    assert resp.status_code == 415


def test_put_thumbnail_too_large(client, monkeypatch):
    monkeypatch.setattr(ProjectService, "user_owns_project", lambda *_: True)
    monkeypatch.setattr(ProjectService, "project_exists", lambda *_: True)

    big = b"x" * (5 * 1024 * 1024 + 1)
    resp = client.put(
        "/api/projects/1/thumbnail",
        files={"file": ("x.png", big, "image/png")},
    )
    assert resp.status_code == 413


def test_put_thumbnail_success(client, monkeypatch):
    monkeypatch.setattr(ProjectService, "user_owns_project", lambda *_: True)
    monkeypatch.setattr(ProjectService, "project_exists", lambda *_: True)

    now = datetime(2024, 1, 1, tzinfo=timezone.utc)

    def _fake_set_thumbnail(self, project_id, **kwargs):
        return {
            "project_id": project_id,
            "has_thumbnail": True,
            "thumbnail_updated_at": now.isoformat(),
            "thumbnail_endpoint": f"/api/projects/{project_id}/thumbnail",
            "content_type": kwargs["content_type"],
            "size_bytes": kwargs["size_bytes"],
            "etag": kwargs["etag"],
        }

    monkeypatch.setattr(ProjectService, "set_thumbnail", _fake_set_thumbnail)

    resp = client.put(
        "/api/projects/1/thumbnail",
        files={"file": ("x.png", b"pngbytes", "image/png")},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["project_id"] == 1
    assert body["has_thumbnail"] is True
    assert body["thumbnail_endpoint"] == "/api/projects/1/thumbnail"
    assert body["content_type"] == "image/png"
    assert body["size_bytes"] == len(b"pngbytes")
    assert isinstance(body["etag"], str) and len(body["etag"]) > 0