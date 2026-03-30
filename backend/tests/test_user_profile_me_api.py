from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.api.dependencies import get_current_user
from src.api.main import app
from src.models.database import get_db
from src.models.database import Base
from src.models.orm.user import User

PROFILE_PAYLOAD = {
    "first_name": "Kussh",
    "last_name": "Satija",
    "phone": "2505550123",
    "city": "Kelowna",
    "state": "British Columbia",
    "country": "Canada",
    "linkedin_url": "https://linkedin.com/in/kussh",
    "github_url": "https://github.com/kussh",
    "portfolio_url": "https://kussh.dev",
    "summary": "Computer science student building data-driven products.",
}
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_current_user():
    return User(
        id=1,
        email="kussh@example.com",
        is_active=True,
    )


client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user


def teardown_function():
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_get_my_profile_returns_404_when_missing():
    response = client.get("/api/user-profiles/me")
    assert response.status_code == 404


def test_put_my_profile_creates_profile():
    response = client.put("/api/user-profiles/me", json=PROFILE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert data["first_name"] == PROFILE_PAYLOAD["first_name"]
    assert data["last_name"] == PROFILE_PAYLOAD["last_name"]
    assert data["city"] == PROFILE_PAYLOAD["city"]


def test_get_my_profile_returns_profile():
    client.put("/api/user-profiles/me", json=PROFILE_PAYLOAD)
    response = client.get("/api/user-profiles/me")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert data["first_name"] == PROFILE_PAYLOAD["first_name"]
    assert data["github_url"] == PROFILE_PAYLOAD["github_url"]


def test_put_my_profile_updates_existing_profile():
    client.put("/api/user-profiles/me", json=PROFILE_PAYLOAD)
    updated_payload = {
        **PROFILE_PAYLOAD,
        "city": "Vancouver",
        "summary": "Updated summary",
    }
    response = client.put("/api/user-profiles/me", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert data["city"] == "Vancouver"
    assert data["summary"] == "Updated summary"


def test_get_my_profile_requires_auth():
    app.dependency_overrides.pop(get_current_user, None)
    response = client.get("/api/user-profiles/me")
    assert response.status_code in {401, 403}
