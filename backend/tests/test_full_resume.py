"""Tests for the full resume composition and export feature."""

import json
import sys
from datetime import date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models.database import Base, get_db

# Import all ORM models so Base.metadata has every table definition
# before any create_all() call.
import src.models.orm  # noqa: F401 – registers all ORM classes

from src.models.orm.education import Education
from src.models.orm.experience import Experience, ExperienceType
from src.models.orm.project import Project
from src.models.orm.resume import ResumeItem
from src.models.orm.skill import ProjectSkill, Skill
from src.models.orm.user import User
from src.models.orm.user_profile import UserProfile


# ---------------------------------------------------------------------------
# Shared fake PDF bytes used by weasyprint mock
# ---------------------------------------------------------------------------
_FAKE_PDF = b"%PDF-1.4 mock content\n%%EOF"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_session():
    """In-memory SQLite session that shares a single connection (StaticPool).

    Using StaticPool guarantees that Base.metadata.create_all() and the
    session created afterwards both operate on the SAME SQLite in-memory
    database, even when FastAPI/Starlette runs the request handler in a
    separate thread.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Persist and return a test user."""
    user = User(email="test@example.com", password_hash="hashed", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_profile(db_session, test_user):
    """Persist a full user profile for test_user."""
    profile = UserProfile(
        user_id=test_user.id,
        first_name="Jane",
        last_name="Doe",
        phone="555-1234",
        city="Vancouver",
        state="BC",
        linkedin_url="https://linkedin.com/in/janedoe",
        github_url="https://github.com/janedoe",
        summary="Experienced software engineer.",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def test_education(db_session, test_user):
    """Persist an education record for test_user."""
    edu = Education(
        user_id=test_user.id,
        institution="UBC",
        degree="BSc",
        field_of_study="Computer Science",
        start_date=date(2018, 9, 1),
        end_date=date(2022, 5, 31),
        is_current=False,
        gpa=3.85,
        location="Vancouver, BC",
    )
    db_session.add(edu)
    db_session.commit()
    db_session.refresh(edu)
    return edu


@pytest.fixture
def test_experience(db_session, test_user):
    """Persist a work experience record for test_user."""
    exp = Experience(
        user_id=test_user.id,
        experience_type=ExperienceType.WORK.value,
        company_name="Acme Corp",
        job_title="Software Engineer",
        location="Remote",
        is_remote=True,
        start_date=date(2022, 6, 1),
        is_current=True,
        responsibilities=json.dumps(["Built REST APIs", "Mentored junior devs"]),
        achievements=json.dumps(["Reduced latency by 30%"]),
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


@pytest.fixture
def test_project_with_resume(db_session, test_user):
    """Persist a project, a resume item, and skills for test_user."""
    project = Project(
        user_id=test_user.id,
        name="MyApp",
        root_path="/tmp/myapp",
        source_type="upload",
        created_at=datetime(2023, 3, 15),
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    resume_item = ResumeItem(
        project_id=project.id,
        title="MyApp",
        highlights=["Implemented feature X", "Deployed to AWS"],
    )
    db_session.add(resume_item)

    skill = Skill(name="Python", category="Languages")
    db_session.add(skill)
    db_session.flush()

    project_skill = ProjectSkill(
        project_id=project.id,
        skill_id=skill.id,
        frequency=10,
    )
    db_session.add(project_skill)
    db_session.commit()
    return project


# ---------------------------------------------------------------------------
# Service helpers
# ---------------------------------------------------------------------------


def make_service(db_session):
    from src.services.full_resume_service import FullResumeService

    return FullResumeService(db_session)


def _mock_weasyprint(mock_obj=None):
    """Context manager that patches sys.modules["weasyprint"] with a mock.

    Handles the case where weasyprint's GTK native libraries are absent
    (common on Windows developer machines).
    """
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        m = mock_obj if mock_obj is not None else MagicMock()
        m.HTML.return_value.write_pdf.return_value = _FAKE_PDF
        orig = sys.modules.get("weasyprint")
        sys.modules["weasyprint"] = m
        try:
            yield m
        finally:
            if orig is None:
                sys.modules.pop("weasyprint", None)
            else:
                sys.modules["weasyprint"] = orig

    return _ctx()


# ---------------------------------------------------------------------------
# compose_resume tests
# ---------------------------------------------------------------------------


class TestComposeResume:
    def test_compose_resume_full_data(
        self,
        db_session,
        test_user,
        test_profile,
        test_education,
        test_experience,
        test_project_with_resume,
    ):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)

        assert data.contact.name == "Jane Doe"
        assert data.contact.email == "test@example.com"
        assert data.contact.phone == "555-1234"
        assert data.contact.location == "Vancouver, BC"
        assert data.summary == "Experienced software engineer."
        assert len(data.education) == 1
        assert data.education[0].institution == "UBC"
        assert len(data.experience) == 1
        assert data.experience[0].company_name == "Acme Corp"
        assert len(data.projects) == 1
        assert data.projects[0].title == "MyApp"
        assert "Languages" in data.skills
        assert isinstance(data.generated_at, datetime)

    def test_compose_resume_no_profile(self, db_session, test_user):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)

        assert data.contact.name == "Your Name"
        assert data.contact.email == "test@example.com"
        assert data.contact.phone is None
        assert data.contact.location is None
        assert data.contact.linkedin_url is None
        assert data.summary is None

    def test_compose_resume_no_education(
        self, db_session, test_user, test_profile
    ):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)
        assert data.education == []

    def test_compose_resume_no_experience(
        self, db_session, test_user, test_profile
    ):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)
        assert data.experience == []

    def test_compose_resume_no_projects(
        self, db_session, test_user, test_profile
    ):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)
        assert data.projects == []

    def test_compose_resume_project_no_resume_item(self, db_session, test_user):
        """Project with no resume items should still be included with empty highlights."""
        project = Project(
            user_id=test_user.id,
            name="BareProject",
            root_path="/tmp/bare",
            source_type="upload",
            created_at=datetime(2024, 1, 1),
        )
        db_session.add(project)
        db_session.commit()

        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)

        assert len(data.projects) == 1
        assert data.projects[0].title == "BareProject"
        assert data.projects[0].highlights == []

    def test_compose_resume_user_not_found(self, db_session):
        svc = make_service(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.compose_resume(9999)


# ---------------------------------------------------------------------------
# export_markdown tests
# ---------------------------------------------------------------------------


class TestExportMarkdown:
    def test_export_markdown_format(
        self,
        db_session,
        test_user,
        test_profile,
        test_education,
        test_experience,
        test_project_with_resume,
    ):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)
        md = svc.export_markdown(data)

        assert "# " in md
        assert "## Education" in md
        assert "## Experience" in md
        assert "## Projects" in md
        assert "## Technical Skills" in md

    def test_export_markdown_missing_sections(self, db_session, test_user):
        """When sections are empty, their headings must be absent."""
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)
        md = svc.export_markdown(data)

        assert "## Education" not in md
        assert "## Experience" not in md
        assert "## Projects" not in md
        assert "## Technical Skills" not in md
        assert "## Summary" not in md

    def test_export_markdown_contains_name(
        self, db_session, test_user, test_profile
    ):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)
        md = svc.export_markdown(data)
        assert "Jane Doe" in md

    def test_export_markdown_contact_row(
        self, db_session, test_user, test_profile
    ):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)
        md = svc.export_markdown(data)
        assert "test@example.com" in md
        assert "555-1234" in md


# ---------------------------------------------------------------------------
# export_html tests
# ---------------------------------------------------------------------------


class TestExportHTML:
    def test_export_html_format(
        self,
        db_session,
        test_user,
        test_profile,
        test_education,
        test_experience,
        test_project_with_resume,
    ):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)
        html = svc.export_html(data)

        assert "<html" in html
        assert "<body" in html
        assert "Jane Doe" in html
        assert "Education" in html
        assert "Experience" in html
        assert "Projects" in html

    def test_export_html_no_sections(self, db_session, test_user):
        """With no data, HTML should still be valid with just the header."""
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)
        html = svc.export_html(data)
        assert "<html" in html
        assert "Your Name" in html


# ---------------------------------------------------------------------------
# export_pdf tests  (weasyprint is mocked via sys.modules so GTK is not needed)
# ---------------------------------------------------------------------------


class TestExportPDF:
    def test_export_pdf_returns_bytes(
        self,
        db_session,
        test_user,
        test_profile,
    ):
        svc = make_service(db_session)
        data = svc.compose_resume(test_user.id)

        with _mock_weasyprint() as mock_wp:
            pdf = svc.export_pdf(data)
            mock_wp.HTML.assert_called_once()

        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client(db_session, test_user):
    """TestClient with the DB session and auth overridden to use in-memory SQLite."""
    from src.api.main import app
    from src.api.dependencies import get_current_user

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestFullResumeAPI:
    def test_api_get_resume_json_200(
        self,
        api_client,
        test_user,
        test_profile,
        test_education,
        test_experience,
        test_project_with_resume,
    ):
        response = api_client.get(f"/api/users/{test_user.id}/resume")
        assert response.status_code == 200
        body = response.json()
        assert "contact" in body
        assert "education" in body
        assert "experience" in body
        assert "projects" in body
        assert "skills" in body
        assert body["contact"]["name"] == "Jane Doe"

    def test_api_get_resume_user_not_found(self, api_client):
        response = api_client.get("/api/users/9999/resume")
        assert response.status_code == 404

    def test_api_export_pdf(
        self,
        api_client,
        test_user,
        test_profile,
    ):
        with _mock_weasyprint():
            response = api_client.get(
                f"/api/users/{test_user.id}/resume/export?format=pdf"
            )
        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
        assert response.content[:4] == b"%PDF"

    def test_api_export_markdown(
        self,
        api_client,
        test_user,
        test_profile,
    ):
        response = api_client.get(
            f"/api/users/{test_user.id}/resume/export?format=markdown"
        )
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        assert "# " in response.text

    def test_api_export_html(
        self,
        api_client,
        test_user,
        test_profile,
    ):
        response = api_client.get(
            f"/api/users/{test_user.id}/resume/export?format=html"
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<html" in response.text

    def test_api_export_invalid_format(
        self,
        api_client,
        test_user,
    ):
        response = api_client.get(
            f"/api/users/{test_user.id}/resume/export?format=docx"
        )
        assert response.status_code == 400

    def test_api_export_user_not_found(self, api_client):
        response = api_client.get("/api/users/9999/resume/export?format=html")
        assert response.status_code == 404
