from datetime import datetime, timezone

from src.services.project_service import ProjectService


def test_set_thumbnail_success(client, monkeypatch):
    def fake_exists(self, project_id):
        return True

    def fake_set_thumbnail(self, project_id, **kwargs):
        return {
            "project_id": project_id,
            "has_thumbnail": True,
            "thumbnail_updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "thumbnail_endpoint": f"/api/projects/{project_id}/thumbnail",
        }

    monkeypatch.setattr(ProjectService, "project_exists", fake_exists)
    monkeypatch.setattr(ProjectService, "set_thumbnail", fake_set_thumbnail)

    response = client.put(
        "/api/projects/1/thumbnail",
        files={"file": ("thumb.png", b"fakeimage", "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == 1
    assert data["has_thumbnail"] is True
    assert data["thumbnail_endpoint"] == "/api/projects/1/thumbnail"


def test_set_thumbnail_invalid_type(client, monkeypatch):
    def fake_exists(self, project_id):
        return True

    monkeypatch.setattr(ProjectService, "project_exists", fake_exists)

    response = client.put(
        "/api/projects/1/thumbnail",
        files={"file": ("thumb.txt", b"text", "text/plain")},
    )

    assert response.status_code == 400


def test_set_thumbnail_project_not_found(client, monkeypatch):
    def fake_exists(self, project_id):
        return False

    monkeypatch.setattr(ProjectService, "project_exists", fake_exists)

    response = client.put(
        "/api/projects/999/thumbnail",
        files={"file": ("thumb.png", b"fakeimage", "image/png")},
    )

    assert response.status_code == 404
