"""Tests for the Portfolio POST /generate endpoint, service, and generator."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from src.api.main import app
from src.services.portfolio_service import PortfolioService
from src.core.generators.portfolio import (
    generate_portfolio,
    _generate_template_based,
    _build_ai_context,
)

client = TestClient(app)


# --- Generator layer tests ---


def test_generate_portfolio_template_based():
    """Template fallback produces correct title and summary format."""
    result = _generate_template_based(
        user_name="Jane Doe",
        projects_data=[
            {"name": "WebApp", "languages": ["Python", "JavaScript"], "frameworks": ["FastAPI"]},
            {"name": "MobileApp", "languages": ["Kotlin"], "frameworks": ["Android"]},
        ],
        aggregated_skills={"Backend": ["REST API", "SQL"], "Frontend": ["React"]},
    )

    assert result["title"] == "Jane Doe's Software Engineering Portfolio"
    assert "2 projects" in result["summary"]
    assert "Python" in result["summary"]


def test_generate_portfolio_template_based_no_projects():
    """Template handles empty projects list."""
    result = _generate_template_based(
        user_name="John",
        projects_data=[],
        aggregated_skills={},
    )

    assert "John" in result["title"]
    assert "0 projects" in result["summary"]


def test_build_portfolio_ai_context():
    """AI context string includes all expected data."""
    context = _build_ai_context(
        user_name="Jane Doe",
        projects_data=[
            {
                "name": "MyApp",
                "languages": ["Python"],
                "frameworks": ["FastAPI"],
                "resume_highlights": ["Built a REST API"],
            }
        ],
        aggregated_skills={"Backend": ["REST API", "SQL"]},
        experiences=[
            {
                "company_name": "Acme",
                "job_title": "Engineer",
                "start_date": "2023-01-01",
                "end_date": None,
                "description": "Built stuff",
            }
        ],
        profile_summary="Experienced developer",
    )

    assert "Jane Doe" in context
    assert "MyApp" in context
    assert "Python" in context
    assert "Backend" in context
    assert "REST API" in context
    assert "Acme" in context
    assert "Engineer" in context
    assert "Experienced developer" in context


def test_generate_portfolio_falls_back_to_template_when_ai_disabled():
    """generate_portfolio uses template when use_ai=False."""
    result = generate_portfolio(
        user_name="Test User",
        projects_data=[{"name": "Proj", "languages": ["Go"], "frameworks": []}],
        aggregated_skills={"Backend": ["Go"]},
        experiences=[],
        use_ai=False,
    )

    assert "title" in result
    assert "summary" in result
    assert "Test User" in result["title"]


def test_generate_portfolio_falls_back_to_template_when_no_api_key():
    """generate_portfolio uses template when api_key is None."""
    result = generate_portfolio(
        user_name="Test User",
        projects_data=[],
        aggregated_skills={},
        experiences=[],
        use_ai=True,
        api_key=None,
    )

    assert "title" in result
    assert "summary" in result


# --- Service layer tests ---


def _make_service_with_mocks(
    projects=None,
    profile=None,
    experiences=None,
    existing_portfolio=None,
):
    """Helper to create a PortfolioService with mocked repositories."""
    now = datetime.now(timezone.utc)

    created_portfolios = []

    def fake_create(obj):
        obj.id = 1
        obj.created_at = now
        obj.updated_at = now
        created_portfolios.append(obj)
        return obj

    def fake_update(obj):
        obj.updated_at = now
        return obj

    service = PortfolioService(db=None)
    service.project_repo = SimpleNamespace(
        get_by_user_id=lambda uid: projects or [],
        get_languages=lambda pid: ["Python"],
        get_frameworks=lambda pid: ["FastAPI"],
    )
    service.skill_repo = SimpleNamespace(
        get_grouped_by_category=lambda pid: {},
    )
    service.resume_repo = SimpleNamespace(
        get_latest=lambda pid: None,
    )
    service.profile_repo = SimpleNamespace(
        get_by_user_id=lambda uid: profile,
    )
    service.experience_repo = SimpleNamespace(
        get_by_user=lambda uid: experiences or [],
    )
    service.portfolio_repo = SimpleNamespace(
        get_by_user_id=lambda uid: existing_portfolio,
        create=fake_create,
        update=fake_update,
    )

    return service, created_portfolios


@patch("src.services.portfolio_service.generate_portfolio")
@patch("src.services.portfolio_service.settings")
def test_generate_portfolio_no_projects(mock_settings, mock_gen):
    """Service creates portfolio even when user has no projects."""
    mock_settings.ai_resume_generation = False
    mock_settings.openai_api_key = None
    mock_settings.ai_model = "gpt-4o-mini"
    mock_settings.ai_temperature = 0.7
    mock_settings.ai_max_tokens = 500
    mock_gen.return_value = {"title": "My Portfolio", "summary": "A developer."}

    service, created = _make_service_with_mocks(projects=[])
    mock_user = SimpleNamespace(id=1, email="test@example.com")

    result = service.generate_portfolio(mock_user)

    assert result.user_id == 1
    assert result.title == "My Portfolio"
    assert result.content["projects"] == []
    assert len(created) == 1


@patch("src.services.portfolio_service.generate_portfolio")
@patch("src.services.portfolio_service.settings")
def test_generate_portfolio_with_projects(mock_settings, mock_gen):
    """Service gathers project data and includes it in content."""
    mock_settings.ai_resume_generation = False
    mock_settings.openai_api_key = None
    mock_settings.ai_model = "gpt-4o-mini"
    mock_settings.ai_temperature = 0.7
    mock_settings.ai_max_tokens = 500
    mock_gen.return_value = {"title": "Engineer Portfolio", "summary": "Great dev."}

    projects = [
        SimpleNamespace(id=10, name="ProjectA"),
        SimpleNamespace(id=20, name="ProjectB"),
    ]

    service, _ = _make_service_with_mocks(projects=projects)
    mock_user = SimpleNamespace(id=1, email="test@example.com")

    result = service.generate_portfolio(mock_user)

    assert len(result.content["projects"]) == 2
    assert result.content["projects"][0]["name"] == "ProjectA"
    assert result.content["projects"][1]["name"] == "ProjectB"
    assert "Python" in result.content["projects"][0]["languages"]


@patch("src.services.portfolio_service.generate_portfolio")
@patch("src.services.portfolio_service.settings")
def test_generate_portfolio_upsert_updates_existing(mock_settings, mock_gen):
    """Service updates existing portfolio instead of creating a new one."""
    mock_settings.ai_resume_generation = False
    mock_settings.openai_api_key = None
    mock_settings.ai_model = "gpt-4o-mini"
    mock_settings.ai_temperature = 0.7
    mock_settings.ai_max_tokens = 500
    mock_gen.return_value = {"title": "Updated", "summary": "Updated summary."}

    now = datetime.now(timezone.utc)
    existing = SimpleNamespace(
        id=5, user_id=1, title="Old", summary="Old summary",
        content={}, created_at=now, updated_at=now,
    )

    service, created = _make_service_with_mocks(existing_portfolio=existing)
    mock_user = SimpleNamespace(id=1, email="test@example.com")

    result = service.generate_portfolio(mock_user)

    assert result.id == 5
    assert result.title == "Updated"
    assert result.summary == "Updated summary."
    assert len(created) == 0  # Should not create, should update


@patch("src.services.portfolio_service.generate_portfolio")
@patch("src.services.portfolio_service.settings")
def test_generate_portfolio_uses_profile_name(mock_settings, mock_gen):
    """Service uses profile first_name + last_name when available."""
    mock_settings.ai_resume_generation = False
    mock_settings.openai_api_key = None
    mock_settings.ai_model = "gpt-4o-mini"
    mock_settings.ai_temperature = 0.7
    mock_settings.ai_max_tokens = 500
    mock_gen.return_value = {"title": "Portfolio", "summary": "Summary."}

    profile = SimpleNamespace(
        first_name="Jane", last_name="Doe", summary="Senior dev",
    )

    service, _ = _make_service_with_mocks(profile=profile)
    mock_user = SimpleNamespace(id=1, email="jane@example.com")

    service.generate_portfolio(mock_user)

    # Verify generate_portfolio was called with user_name="Jane Doe"
    call_args = mock_gen.call_args
    assert call_args.kwargs["user_name"] == "Jane Doe"
    assert call_args.kwargs["profile_summary"] == "Senior dev"


@patch("src.services.portfolio_service.generate_portfolio")
@patch("src.services.portfolio_service.settings")
def test_generate_portfolio_skills_deduplicated(mock_settings, mock_gen):
    """Service deduplicates aggregated skills across projects."""
    mock_settings.ai_resume_generation = False
    mock_settings.openai_api_key = None
    mock_settings.ai_model = "gpt-4o-mini"
    mock_settings.ai_temperature = 0.7
    mock_settings.ai_max_tokens = 500
    mock_gen.return_value = {"title": "Portfolio", "summary": "Summary."}

    projects = [
        SimpleNamespace(id=10, name="ProjA"),
        SimpleNamespace(id=20, name="ProjB"),
    ]

    # Both projects return the same skill
    skill_a = SimpleNamespace(skill=SimpleNamespace(name="REST API"))
    skill_b = SimpleNamespace(skill=SimpleNamespace(name="REST API"))

    service, _ = _make_service_with_mocks(projects=projects)
    service.skill_repo = SimpleNamespace(
        get_grouped_by_category=lambda pid: {"Backend": [skill_a if pid == 10 else skill_b]},
    )
    mock_user = SimpleNamespace(id=1, email="test@example.com")

    result = service.generate_portfolio(mock_user)

    # "REST API" should appear only once
    assert result.content["aggregated_skills"]["Backend"] == ["REST API"]


# --- Route / endpoint tests ---


def test_generate_portfolio_requires_auth():
    """POST /api/portfolio/generate returns 401 without auth token."""
    response = client.post("/api/portfolio/generate")

    assert response.status_code == 401


def test_generate_portfolio_rejects_invalid_token():
    """POST /api/portfolio/generate returns 401 with invalid token."""
    headers = {"Authorization": "Bearer fake.token.123"}
    response = client.post("/api/portfolio/generate", headers=headers)

    assert response.status_code == 401


@patch("src.api.routes.portfolio.PortfolioService")
def test_generate_portfolio_endpoint_success(mock_service_class):
    """POST /api/portfolio/generate returns 201 with portfolio data."""
    from src.api.dependencies import get_current_user

    now = datetime.now(timezone.utc)
    fake_user = SimpleNamespace(id=10, email="test@example.com", is_active=True)

    mock_service = MagicMock()
    mock_service.generate_portfolio.return_value = SimpleNamespace(
        id=1,
        user_id=10,
        title="Generated Portfolio",
        summary="A professional summary.",
        content={"projects": [], "aggregated_skills": {}, "experiences": []},
        created_at=now,
        updated_at=now,
    )
    mock_service_class.return_value = mock_service

    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        response = client.post("/api/portfolio/generate")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Generated Portfolio"
    assert data["summary"] == "A professional summary."
    assert "projects" in data["content"]


@patch("src.api.routes.portfolio.PortfolioService")
def test_generate_portfolio_endpoint_server_error(mock_service_class):
    """POST /api/portfolio/generate returns 500 when service raises."""
    from src.api.dependencies import get_current_user

    fake_user = SimpleNamespace(id=10, email="test@example.com", is_active=True)

    mock_service = MagicMock()
    mock_service.generate_portfolio.side_effect = Exception("DB error")
    mock_service_class.return_value = mock_service

    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        response = client.post("/api/portfolio/generate")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 500
    assert "failed" in response.json()["detail"].lower()
