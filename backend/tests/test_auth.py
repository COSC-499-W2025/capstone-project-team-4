from fastapi.testclient import TestClient
from src.api.main import app
import pytest

client = TestClient(app)


# Generate a unique email every time so tests don't fail
@pytest.fixture
def test_user_data():
    import time

    # Creates "test_232323_@example.com"
    return {
        "email": f"test_{int(time.time())}@example.com",
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
    login_data = {
        "username": registered_user["email"],
        "password": "WRONG_PASSWORD"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json().get("detail", "")

def test_login_nonexistent_user():
    """Should fail with 401 when user doesn't exist"""
    login_data = {
        "username": "ghost@example.com",
        "password": "password123"
    }
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