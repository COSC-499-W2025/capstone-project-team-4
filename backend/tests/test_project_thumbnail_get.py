from __future__ import annotations

from contextlib import asynccontextmanager
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
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, is_active=True
    )
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.router.lifespan_context = original_lifespan


def test_get_thumbnail_404_when_missing(client, monkeypatch):
    monkeypatch.setattr(ProjectService, "user_owns_project", lambda *_: True)
    monkeypatch.setattr(ProjectService, "project_exists", lambda *_: True)
    monkeypatch.setattr(ProjectService, "get_thumbnail", lambda *_: None)

    resp = client.get("/api/projects/1/thumbnail")
    assert resp.status_code == 404


def test_get_thumbnail_returns_bytes_and_headers(client, monkeypatch):
    monkeypatch.setattr(ProjectService, "user_owns_project", lambda *_: True)
    monkeypatch.setattr(ProjectService, "project_exists", lambda *_: True)
    data = b"jpegbytes"
    monkeypatch.setattr(
        ProjectService, "get_thumbnail", lambda *_: (data, "image/jpeg", "abc123")
    )

    resp = client.get("/api/projects/1/thumbnail")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/jpeg")
    assert resp.headers.get("etag") == "abc123"
    assert resp.content == data


def test_get_thumbnail_304_if_etag_matches(client, monkeypatch):
    monkeypatch.setattr(ProjectService, "user_owns_project", lambda *_: True)
    monkeypatch.setattr(ProjectService, "project_exists", lambda *_: True)
    data = b"pngbytes"
    monkeypatch.setattr(
        ProjectService, "get_thumbnail", lambda *_: (data, "image/png", "etag123")
    )

    resp = client.get("/api/projects/1/thumbnail", headers={"If-None-Match": "etag123"})
    assert resp.status_code == 304
    assert resp.content == b""
    assert resp.headers.get("etag") == "etag123"
