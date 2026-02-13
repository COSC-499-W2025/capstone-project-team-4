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
    EducationBase,
    EducationCreate,
    EducationUpdate,
    EducationResponse,
)
from src.repositories.education_repository import EducationRepository
@pytest.fixture
def db_session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user and return it."""
    user = User(
        email="student@example.com",
        password_hash="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def education_repo(db_session):
    """Return an EducationRepository bound to the test session."""
    return EducationRepository(db_session)


# ORM model tests

class TestEducationModel:
    """Tests for the Education ORM model."""

    def test_create_education_record(self, db_session, test_user):
        """Education row can be persisted with required fields."""
        edu = Education(
            user_id=test_user.id,
            institution="University of British Columbia",
            degree="Bachelor of Science",
            field_of_study="Computer Science",
            start_date=date(2020, 9, 1),
        )
        db_session.add(edu)
        db_session.commit()
        db_session.refresh(edu)

        assert edu.id is not None
        assert edu.user_id == test_user.id
        assert edu.institution == "University of British Columbia"
        assert edu.degree == "Bachelor of Science"
        assert edu.field_of_study == "Computer Science"
        assert edu.start_date == date(2020, 9, 1)

    def test_optional_fields_default_to_none(self, db_session, test_user):
        """Optional columns default to None / False."""
        edu = Education(
            user_id=test_user.id,
            institution="MIT",
            degree="Master of Science",
            field_of_study="AI",
            start_date=date(2022, 1, 15),
        )
        db_session.add(edu)
        db_session.commit()
        db_session.refresh(edu)

        assert edu.end_date is None
        assert edu.is_current is False
        assert edu.gpa is None
        assert edu.location is None
        assert edu.description is None
        assert edu.honors is None
        assert edu.activities is None

    def test_all_fields_persisted(self, db_session, test_user):
        """All columns round-trip correctly."""
        edu = Education(
            user_id=test_user.id,
            institution="Stanford University",
            degree="Bachelor of Arts",
            field_of_study="Mathematics",
            start_date=date(2018, 9, 1),
            end_date=date(2022, 6, 15),
            is_current=False,
            gpa=3.85,
            location="Stanford, CA",
            description="Focus on applied mathematics",
            honors="Magna Cum Laude, Dean's List",
            activities="Math Club, Debate Team",
        )
        db_session.add(edu)
        db_session.commit()
        db_session.refresh(edu)

        assert edu.end_date == date(2022, 6, 15)
        assert edu.is_current is False
        assert edu.gpa == pytest.approx(3.85)
        assert edu.location == "Stanford, CA"
        assert edu.description == "Focus on applied mathematics"
        assert edu.honors == "Magna Cum Laude, Dean's List"
        assert edu.activities == "Math Club, Debate Team"

    def test_timestamps_auto_set(self, db_session, test_user):
        """created_at and updated_at are populated automatically."""
        edu = Education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="Physics",
            start_date=date(2021, 9, 1),
        )
        db_session.add(edu)
        db_session.commit()
        db_session.refresh(edu)

        assert edu.created_at is not None
        assert edu.updated_at is not None

    def test_user_relationship(self, db_session, test_user):
        """Education.user navigates back to the owning User."""
        edu = Education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2020, 9, 1),
        )
        db_session.add(edu)
        db_session.commit()
        db_session.refresh(edu)

        assert edu.user.id == test_user.id
        assert edu.user.email == "student@example.com"

    def test_user_educations_relationship(self, db_session, test_user):
        """User.educations returns associated education entries."""
        edu1 = Education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2018, 9, 1),
        )
        edu2 = Education(
            user_id=test_user.id,
            institution="MIT",
            degree="MSc",
            field_of_study="AI",
            start_date=date(2022, 9, 1),
        )
        db_session.add_all([edu1, edu2])
        db_session.commit()
        db_session.refresh(test_user)

        assert len(test_user.educations) == 2

    def test_cascade_delete(self, db_session, test_user):
        """Deleting a user cascades to their education entries."""
        edu = Education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2020, 9, 1),
        )
        db_session.add(edu)
        db_session.commit()
        edu_id = edu.id

        db_session.delete(test_user)
        db_session.commit()

        assert db_session.get(Education, edu_id) is None

    def test_repr(self, db_session, test_user):
        """__repr__ contains key identifying info."""
        edu = Education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2020, 9, 1),
        )
        db_session.add(edu)
        db_session.commit()

        r = repr(edu)
        assert "UBC" in r
        assert "BSc" in r
        assert "CS" in r

# Pydantic schema tests

class TestEducationSchemas:
    """Tests for Education Pydantic schemas."""

    def test_education_create_required_fields(self):
        """EducationCreate validates required fields."""
        schema = EducationCreate(
            institution="UBC",
            degree="BSc",
            field_of_study="Computer Science",
            start_date=date(2020, 9, 1),
        )
        assert schema.institution == "UBC"
        assert schema.degree == "BSc"
        assert schema.field_of_study == "Computer Science"
        assert schema.is_current is False
        assert schema.gpa is None

    def test_education_create_all_fields(self):
        """EducationCreate accepts all optional fields."""
        schema = EducationCreate(
            institution="Stanford",
            degree="Master of Science",
            field_of_study="AI",
            start_date=date(2022, 9, 1),
            end_date=date(2024, 6, 15),
            is_current=False,
            gpa=3.9,
            location="Stanford, CA",
            description="ML research focus",
            honors="Summa Cum Laude",
            activities="AI Lab, Robotics Club",
        )
        assert schema.gpa == pytest.approx(3.9)
        assert schema.location == "Stanford, CA"
        assert schema.honors == "Summa Cum Laude"
        assert schema.activities == "AI Lab, Robotics Club"

    def test_education_create_missing_required_field_raises(self):
        """EducationCreate rejects missing required fields."""
        with pytest.raises(Exception):
            EducationCreate(
                institution="UBC",
                # degree missing
                field_of_study="CS",
                start_date=date(2020, 9, 1),
            )

    def test_education_create_empty_institution_rejected(self):
        """EducationCreate rejects empty institution string."""
        with pytest.raises(Exception):
            EducationCreate(
                institution="",
                degree="BSc",
                field_of_study="CS",
                start_date=date(2020, 9, 1),
            )

    def test_education_create_gpa_validation_upper_bound(self):
        """EducationCreate rejects GPA above 4.0."""
        with pytest.raises(Exception):
            EducationCreate(
                institution="UBC",
                degree="BSc",
                field_of_study="CS",
                start_date=date(2020, 9, 1),
                gpa=4.5,
            )

    def test_education_create_gpa_validation_lower_bound(self):
        """EducationCreate rejects negative GPA."""
        with pytest.raises(Exception):
            EducationCreate(
                institution="UBC",
                degree="BSc",
                field_of_study="CS",
                start_date=date(2020, 9, 1),
                gpa=-0.1,
            )

    def test_education_update_all_optional(self):
        """EducationUpdate allows all fields to be None."""
        schema = EducationUpdate()
        assert schema.institution is None
        assert schema.degree is None
        assert schema.gpa is None

    def test_education_update_partial(self):
        """EducationUpdate accepts partial updates."""
        schema = EducationUpdate(gpa=3.5, is_current=True)
        assert schema.gpa == pytest.approx(3.5)
        assert schema.is_current is True
        assert schema.institution is None

    def test_education_response_from_attributes(self):
        """EducationResponse can be built from ORM-like object."""
        now = datetime.now(timezone.utc)
        obj = SimpleNamespace(
            id=1,
            user_id=10,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2020, 9, 1),
            end_date=None,
            is_current=True,
            gpa=3.7,
            location="Vancouver, BC",
            description=None,
            honors=None,
            activities=None,
            created_at=now,
            updated_at=now,
        )
        response = EducationResponse.model_validate(obj, from_attributes=True)
        assert response.id == 1
        assert response.user_id == 10
        assert response.institution == "UBC"
        assert response.is_current is True
        assert response.created_at == now


# Repository tests

class TestEducationRepository:
    """Tests for EducationRepository."""

    def test_create_education(self, education_repo, test_user):
        """create_education persists and returns the new record."""
        edu = education_repo.create_education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="Computer Science",
            start_date=date(2020, 9, 1),
        )
        assert edu.id is not None
        assert edu.institution == "UBC"
        assert edu.user_id == test_user.id

    def test_create_education_with_all_fields(self, education_repo, test_user):
        """create_education handles all optional parameters."""
        edu = education_repo.create_education(
            user_id=test_user.id,
            institution="Stanford",
            degree="MSc",
            field_of_study="AI",
            start_date=date(2022, 9, 1),
            end_date=date(2024, 6, 15),
            is_current=False,
            gpa=3.95,
            location="Stanford, CA",
            description="Machine learning research",
            honors="With Distinction",
            activities="AI Lab",
        )
        assert edu.gpa == pytest.approx(3.95)
        assert edu.location == "Stanford, CA"
        assert edu.honors == "With Distinction"

    def test_get_by_user(self, education_repo, test_user):
        """get_by_user returns all education entries for a user ordered by start_date desc."""
        education_repo.create_education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2018, 9, 1),
        )
        education_repo.create_education(
            user_id=test_user.id,
            institution="MIT",
            degree="MSc",
            field_of_study="AI",
            start_date=date(2022, 9, 1),
        )

        results = education_repo.get_by_user(test_user.id)
        assert len(results) == 2
        # Ordered by start_date descending
        assert results[0].institution == "MIT"
        assert results[1].institution == "UBC"

    def test_get_by_user_empty(self, education_repo, test_user):
        """get_by_user returns empty list when user has no education entries."""
        results = education_repo.get_by_user(test_user.id)
        assert results == []

    def test_get_by_user_isolation(self, education_repo, db_session):
        """get_by_user only returns entries for the requested user."""
        user_a = User(email="a@example.com", password_hash="h", is_active=True)
        user_b = User(email="b@example.com", password_hash="h", is_active=True)
        db_session.add_all([user_a, user_b])
        db_session.commit()

        education_repo.create_education(
            user_id=user_a.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2020, 9, 1),
        )
        education_repo.create_education(
            user_id=user_b.id,
            institution="MIT",
            degree="MSc",
            field_of_study="AI",
            start_date=date(2022, 9, 1),
        )

        results_a = education_repo.get_by_user(user_a.id)
        assert len(results_a) == 1
        assert results_a[0].institution == "UBC"

    def test_update_education(self, education_repo, test_user):
        """update_education modifies specified fields."""
        edu = education_repo.create_education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2020, 9, 1),
        )

        updated = education_repo.update_education(
            edu.id,
            gpa=3.8,
            honors="Dean's List",
        )
        assert updated is not None
        assert updated.gpa == pytest.approx(3.8)
        assert updated.honors == "Dean's List"
        # Unchanged fields remain
        assert updated.institution == "UBC"

    def test_update_education_nonexistent_returns_none(self, education_repo):
        """update_education returns None for a nonexistent id."""
        result = education_repo.update_education(9999, gpa=3.0)
        assert result is None

    def test_delete_by_user(self, education_repo, test_user):
        """delete_by_user removes all entries for a user and returns count."""
        education_repo.create_education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2018, 9, 1),
        )
        education_repo.create_education(
            user_id=test_user.id,
            institution="MIT",
            degree="MSc",
            field_of_study="AI",
            start_date=date(2022, 9, 1),
        )

        count = education_repo.delete_by_user(test_user.id)
        assert count == 2
        assert education_repo.get_by_user(test_user.id) == []

    def test_delete_by_user_no_entries(self, education_repo, test_user):
        """delete_by_user returns 0 when user has no entries."""
        count = education_repo.delete_by_user(test_user.id)
        assert count == 0

    def test_base_repo_get(self, education_repo, test_user):
        """Inherited get() retrieves by primary key."""
        edu = education_repo.create_education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2020, 9, 1),
        )
        fetched = education_repo.get(edu.id)
        assert fetched is not None
        assert fetched.id == edu.id

    def test_base_repo_delete(self, education_repo, test_user):
        """Inherited delete() removes a single record by id."""
        edu = education_repo.create_education(
            user_id=test_user.id,
            institution="UBC",
            degree="BSc",
            field_of_study="CS",
            start_date=date(2020, 9, 1),
        )
        assert education_repo.delete(edu.id) is True
        assert education_repo.get(edu.id) is None

    def test_base_repo_delete_nonexistent(self, education_repo):
        """Inherited delete() returns False for nonexistent id."""
        assert education_repo.delete(9999) is False
