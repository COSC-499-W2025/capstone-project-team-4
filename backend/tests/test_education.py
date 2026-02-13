"""Unit tests for Education ORM model, Pydantic schemas, and repository."""

import pytest
from datetime import date, datetime, timezone
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.orm.education import Education
from src.models.orm.user import User
from src.models.schemas.education import (
    EducationCreate,
    EducationUpdate,
    EducationResponse,
)
from src.repositories.education_repository import EducationRepository

# Reusable minimal required-field dicts
REQUIRED_FIELDS = {
    "institution": "UBC",
    "degree": "BSc",
    "field_of_study": "CS",
    "start_date": date(2020, 9, 1),
}

ALL_OPTIONAL_FIELDS = {
    "end_date": date(2022, 6, 15),
    "is_current": False,
    "gpa": 3.85,
    "location": "Stanford, CA",
    "description": "Focus on applied mathematics",
    "honors": "Magna Cum Laude, Dean's List",
    "activities": "Math Club, Debate Team",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create and return a persisted test user."""
    user = User(email="student@example.com", password_hash="hashed", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def education_repo(db_session):
    """Return an EducationRepository bound to the test session."""
    return EducationRepository(db_session)


@pytest.fixture
def persisted_education(db_session, test_user):
    """Create and return a persisted Education with only required fields."""
    edu = Education(user_id=test_user.id, **REQUIRED_FIELDS)
    db_session.add(edu)
    db_session.commit()
    db_session.refresh(edu)
    return edu


def _create_via_repo(repo, user_id, **overrides):
    """Helper to create an education entry via repo with defaults + overrides."""
    kwargs = {**REQUIRED_FIELDS, "user_id": user_id, **overrides}
    return repo.create_education(**kwargs)


# ---------------------------------------------------------------------------
# ORM model tests
# ---------------------------------------------------------------------------

class TestEducationModel:
    """Tests for the Education ORM model."""

    def test_create_with_required_fields(self, persisted_education, test_user):
        edu = persisted_education
        assert edu.id is not None
        assert edu.user_id == test_user.id
        assert edu.institution == REQUIRED_FIELDS["institution"]
        assert edu.start_date == REQUIRED_FIELDS["start_date"]

    def test_optional_fields_default_to_none(self, persisted_education):
        for field in ("end_date", "gpa", "location", "description", "honors", "activities"):
            assert getattr(persisted_education, field) is None
        assert persisted_education.is_current is False

    def test_all_fields_persisted(self, db_session, test_user):
        edu = Education(user_id=test_user.id, **REQUIRED_FIELDS, **ALL_OPTIONAL_FIELDS)
        db_session.add(edu)
        db_session.commit()
        db_session.refresh(edu)

        for key, expected in ALL_OPTIONAL_FIELDS.items():
            actual = getattr(edu, key)
            if isinstance(expected, float):
                assert actual == pytest.approx(expected)
            else:
                assert actual == expected

    def test_timestamps_auto_set(self, persisted_education):
        assert persisted_education.created_at is not None
        assert persisted_education.updated_at is not None

    def test_user_relationship(self, persisted_education, test_user):
        assert persisted_education.user.id == test_user.id
        assert persisted_education.user.email == "student@example.com"

    def test_user_educations_relationship(self, db_session, test_user):
        for start_year in (2018, 2022):
            edu = Education(
                user_id=test_user.id,
                **{**REQUIRED_FIELDS, "start_date": date(start_year, 9, 1)},
            )
            db_session.add(edu)
        db_session.commit()
        db_session.refresh(test_user)

        assert len(test_user.educations) == 2

    def test_cascade_delete(self, db_session, test_user, persisted_education):
        edu_id = persisted_education.id
        db_session.delete(test_user)
        db_session.commit()
        assert db_session.get(Education, edu_id) is None

    def test_repr(self, persisted_education):
        r = repr(persisted_education)
        assert "UBC" in r
        assert "BSc" in r
        assert "CS" in r


# ---------------------------------------------------------------------------
# Pydantic schema tests
# ---------------------------------------------------------------------------

class TestEducationSchemas:
    """Tests for Education Pydantic schemas."""

    def test_create_required_fields(self):
        schema = EducationCreate(**REQUIRED_FIELDS)
        assert schema.institution == "UBC"
        assert schema.is_current is False
        assert schema.gpa is None

    def test_create_all_fields(self):
        schema = EducationCreate(**REQUIRED_FIELDS, **ALL_OPTIONAL_FIELDS)
        for key, expected in ALL_OPTIONAL_FIELDS.items():
            actual = getattr(schema, key)
            if isinstance(expected, float):
                assert actual == pytest.approx(expected)
            else:
                assert actual == expected

    def test_create_missing_required_field_raises(self):
        with pytest.raises(Exception):
            EducationCreate(institution="UBC", field_of_study="CS", start_date=date(2020, 9, 1))

    @pytest.mark.parametrize("field", ["institution", "degree", "field_of_study"])
    def test_create_empty_string_rejected(self, field):
        with pytest.raises(Exception):
            EducationCreate(**{**REQUIRED_FIELDS, field: ""})

    @pytest.mark.parametrize("bad_gpa", [4.5, -0.1])
    def test_create_gpa_out_of_range_rejected(self, bad_gpa):
        with pytest.raises(Exception):
            EducationCreate(**REQUIRED_FIELDS, gpa=bad_gpa)

    def test_update_all_optional(self):
        schema = EducationUpdate()
        assert schema.institution is None
        assert schema.degree is None
        assert schema.gpa is None

    def test_update_partial(self):
        schema = EducationUpdate(gpa=3.5, is_current=True)
        assert schema.gpa == pytest.approx(3.5)
        assert schema.is_current is True
        assert schema.institution is None

    def test_response_from_attributes(self):
        now = datetime.now(timezone.utc)
        obj = SimpleNamespace(
            id=1, user_id=10, **REQUIRED_FIELDS,
            end_date=None, is_current=True, gpa=3.7,
            location="Vancouver, BC", description=None,
            honors=None, activities=None,
            created_at=now, updated_at=now,
        )
        response = EducationResponse.model_validate(obj, from_attributes=True)
        assert response.id == 1
        assert response.user_id == 10
        assert response.institution == "UBC"
        assert response.created_at == now


# ---------------------------------------------------------------------------
# Repository tests
# ---------------------------------------------------------------------------

class TestEducationRepository:
    """Tests for EducationRepository."""

    def test_create_education(self, education_repo, test_user):
        edu = _create_via_repo(education_repo, test_user.id)
        assert edu.id is not None
        assert edu.institution == "UBC"
        assert edu.user_id == test_user.id

    def test_create_with_all_fields(self, education_repo, test_user):
        edu = _create_via_repo(education_repo, test_user.id, **ALL_OPTIONAL_FIELDS)
        assert edu.gpa == pytest.approx(3.85)
        assert edu.location == "Stanford, CA"
        assert edu.honors == "Magna Cum Laude, Dean's List"

    def test_get_by_user_ordered_desc(self, education_repo, test_user):
        _create_via_repo(education_repo, test_user.id, institution="UBC", start_date=date(2018, 9, 1))
        _create_via_repo(education_repo, test_user.id, institution="MIT", start_date=date(2022, 9, 1))

        results = education_repo.get_by_user(test_user.id)
        assert len(results) == 2
        assert results[0].institution == "MIT"
        assert results[1].institution == "UBC"

    def test_get_by_user_empty(self, education_repo, test_user):
        assert education_repo.get_by_user(test_user.id) == []

    def test_get_by_user_isolation(self, education_repo, db_session):
        user_a = User(email="a@example.com", password_hash="h", is_active=True)
        user_b = User(email="b@example.com", password_hash="h", is_active=True)
        db_session.add_all([user_a, user_b])
        db_session.commit()

        _create_via_repo(education_repo, user_a.id, institution="UBC")
        _create_via_repo(education_repo, user_b.id, institution="MIT")

        results = education_repo.get_by_user(user_a.id)
        assert len(results) == 1
        assert results[0].institution == "UBC"

    def test_update_education(self, education_repo, test_user):
        edu = _create_via_repo(education_repo, test_user.id)
        updated = education_repo.update_education(edu.id, gpa=3.8, honors="Dean's List")

        assert updated is not None
        assert updated.gpa == pytest.approx(3.8)
        assert updated.honors == "Dean's List"
        assert updated.institution == "UBC"

    def test_update_nonexistent_returns_none(self, education_repo):
        assert education_repo.update_education(9999, gpa=3.0) is None

    def test_delete_by_user(self, education_repo, test_user):
        _create_via_repo(education_repo, test_user.id, start_date=date(2018, 9, 1))
        _create_via_repo(education_repo, test_user.id, start_date=date(2022, 9, 1))

        assert education_repo.delete_by_user(test_user.id) == 2
        assert education_repo.get_by_user(test_user.id) == []

    def test_delete_by_user_no_entries(self, education_repo, test_user):
        assert education_repo.delete_by_user(test_user.id) == 0

    def test_base_get(self, education_repo, test_user):
        edu = _create_via_repo(education_repo, test_user.id)
        fetched = education_repo.get(edu.id)
        assert fetched is not None
        assert fetched.id == edu.id

    def test_base_delete(self, education_repo, test_user):
        edu = _create_via_repo(education_repo, test_user.id)
        assert education_repo.delete(edu.id) is True
        assert education_repo.get(edu.id) is None

    def test_base_delete_nonexistent(self, education_repo):
        assert education_repo.delete(9999) is False
