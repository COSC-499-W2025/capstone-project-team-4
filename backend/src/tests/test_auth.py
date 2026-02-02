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
