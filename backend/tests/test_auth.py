import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


# Generate a unique email every time so tests don't fail
@pytest.fixture
def test_user_data():
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "strongpassword123",
    }


@pytest.fixture
def registered_user(test_user_data):
    """Helper that registers a user and returns the payload"""
    client.post("/api/auth/register", json=test_user_data)
    return test_user_data


def test_full_auth_flow(test_user_data):
    # Registration
    print(f"\nTesting Registration for {test_user_data['email']}...")
    # Registration still expects JSON
    response = client.post("/api/auth/register", json=test_user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert "id" in data

    # Login
    print("Testing Login...")

    login_payload = {
        "username": test_user_data["email"],
        "password": test_user_data["password"],
    }

    response = client.post("/api/auth/login", data=login_payload)

    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    print(f"Got Token: {token[:10]}...")

    # Test Protected route like /me
    print("Testing Protected Route...")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)

    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == test_user_data["email"]

    print("All good!!")


def test_login_invalid_credentials(registered_user):
    """Should fail with 401 when password is wrong"""
    login_data = {"username": registered_user["email"], "password": "WRONG_PASSWORD"}
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json().get("detail", "")


def test_login_nonexistent_user():
    """Should fail with 401 when user doesn't exist"""
    login_data = {"username": "ghost@example.com", "password": "password123"}
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401


def test_protected_route_missing_header():
    """Should fail with 403/401 when no token is provided"""
    response = client.get("/api/auth/me")
    # FastAPI usually returns 403 ("Not authenticated") or 401 depending on setup
    assert response.status_code in [401, 403]


def test_protected_route_invalid_token():
    """Should fail with 401 when token is garbage"""
    headers = {"Authorization": "Bearer faKe.ToKen.123"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


# Now testing the different auth endpoints

# For privacy settings


def test_privacy_settings_authorized(test_user_data):
    # Register and Login
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    my_user_id = me_res.json()["id"]

    response = client.get(f"/api/privacy-settings/{my_user_id}", headers=headers)

    assert response.status_code not in [401, 403]


def test_privacy_settings_forbidden(test_user_data):
    # Register and Login
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    my_user_id = me_res.json()["id"]

    sneaky_target_id = my_user_id + 999
    response = client.get(f"/api/privacy-settings/{sneaky_target_id}", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized"


def test_privacy_settings_unauthenticated():
    # We provide absolutely no headers/tokens
    response = client.get("/api/privacy-settings/1")
    assert response.status_code == 401


# For experiences


def test_get_experiences_authorized(test_user_data):
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    my_user_id = me_res.json()["id"]

    response = client.get(
        f"/api/user-profiles/{my_user_id}/experiences", headers=headers
    )
    assert response.status_code not in [401, 403]


def test_get_experiences_forbidden(test_user_data):
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    my_user_id = me_res.json()["id"]

    sneaky_target_id = my_user_id + 999
    response = client.get(
        f"/api/user-profiles/{sneaky_target_id}/experiences", headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized"


def test_get_experiences_unauthenticated():
    response = client.get("/api/user-profiles/1/experiences")
    assert response.status_code == 401


# POST Experiences


def test_post_experiences_authorized(test_user_data):
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    my_user_id = me_res.json()["id"]

    # Basic payload to pass potential Pydantic validation before auth kicks in
    payload = {"title": "Test Role", "company": "Test Company"}
    response = client.post(
        f"/api/user-profiles/{my_user_id}/experiences", json=payload, headers=headers
    )
    assert response.status_code not in [401, 403]


def test_post_experiences_unauthenticated():
    payload = {"title": "Test Role", "company": "Test Company"}
    response = client.post("/api/user-profiles/1/experiences", json=payload)
    assert response.status_code == 401


# PUT Experiences Auth Tests


def test_put_experiences_authorized(test_user_data):
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    my_user_id = me_res.json()["id"]

    payload = {"title": "Updated Role"}
    response = client.put(
        f"/api/user-profiles/{my_user_id}/experiences/1", json=payload, headers=headers
    )
    assert response.status_code not in [401, 403]


def test_put_experiences_forbidden(test_user_data):
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    my_user_id = me_res.json()["id"]

    sneaky_target_id = my_user_id + 999
    payload = {"title": "Updated Role"}
    response = client.put(
        f"/api/user-profiles/{sneaky_target_id}/experiences/1",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 403


def test_put_experiences_unauthenticated():
    payload = {"title": "Updated Role"}
    response = client.put("/api/user-profiles/1/experiences/1", json=payload)
    assert response.status_code == 401


# DELETE Experiences Auth Tests


def test_delete_experiences_authorized(test_user_data):
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    my_user_id = me_res.json()["id"]

    response = client.delete(
        f"/api/user-profiles/{my_user_id}/experiences/1", headers=headers
    )
    assert response.status_code not in [401, 403]


def test_delete_experiences_forbidden(test_user_data):
    client.post("/api/auth/register", json=test_user_data)
    login_res = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    my_user_id = me_res.json()["id"]

    sneaky_target_id = my_user_id + 999
    response = client.delete(
        f"/api/user-profiles/{sneaky_target_id}/experiences/1", headers=headers
    )
    assert response.status_code == 403


def test_delete_experiences_unauthenticated():
    response = client.delete("/api/user-profiles/1/experiences/1")
    assert response.status_code == 401


# Change password tests


def test_change_password_requires_auth():
    """PATCH /api/auth/change-password returns 401 without auth token."""
    payload = {"old_password": "old_password123", "new_password": "new_password123"}
    # Notice: No headers passed to trigger the Bouncer
    response = client.patch("/api/auth/change-password", json=payload)
    assert response.status_code == 401


@patch("src.api.routes.auth.AuthService")
def test_change_password_success(mock_service_class):
    """PATCH returns 200 when password is changed successfully."""
    from src.api.dependencies import get_current_user

    fake_user = SimpleNamespace(id=1, email="test@example.com")

    # Fake the Service Response (True for success, None for no errors)
    mock_service = MagicMock()
    mock_service.change_password.return_value = (True, None)
    mock_service_class.return_value = mock_service

    # Bypass bouncer from Disney Cars
    app.dependency_overrides[get_current_user] = lambda: fake_user

    payload = {"old_password": "old_password123", "new_password": "new_password123"}

    try:
        response = client.patch("/api/auth/change-password", json=payload)
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    # Verify
    assert response.status_code == 200
    assert response.json()["message"] == "Password updated successfully"


@patch("src.api.routes.auth.AuthService")
def test_change_password_wrong_old_password(mock_service_class):
    """PATCH returns 400 when the old password is incorrect."""
    from src.api.dependencies import get_current_user

    fake_user = SimpleNamespace(id=1, email="test@example.com")

    mock_service = MagicMock()
    mock_service.change_password.return_value = (False, "Incorrect current password.")
    mock_service_class.return_value = mock_service

    app.dependency_overrides[get_current_user] = lambda: fake_user

    payload = {
        "old_password": "wrong_password_guess",
        "new_password": "new_password123",
    }

    try:
        response = client.patch("/api/auth/change-password", json=payload)
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 400
    assert "Incorrect" in response.json()["detail"]
