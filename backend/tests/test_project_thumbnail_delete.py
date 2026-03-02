from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
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
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.router.lifespan_context = original_lifespan


def test_delete_thumbnail_404_when_missing(client, monkeypatch):
    monkeypatch.setattr(ProjectService, "project_exists", lambda *_: True)
    monkeypatch.setattr(ProjectService, "delete_thumbnail", lambda *_: False)

    resp = client.delete("/api/projects/1/thumbnail")
    assert resp.status_code == 404


def test_delete_thumbnail_204_when_deleted(client, monkeypatch):
    monkeypatch.setattr(ProjectService, "project_exists", lambda *_: True)
    monkeypatch.setattr(ProjectService, "delete_thumbnail", lambda *_: True)

    resp = client.delete("/api/projects/1/thumbnail")
    assert resp.status_code == 204