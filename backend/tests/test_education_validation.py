"""Tests for Education schema validation and repository update logic."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from src.models.schemas.education import EducationBase, EducationUpdate
from src.repositories.education_repository import EducationRepository

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))




# ---------------------------------------------------------------------------
# EducationBase / EducationCreate — timeline validation (create path)
# ---------------------------------------------------------------------------

class TestEducationBaseValidation:
    def _base_kwargs(self, **overrides):
        defaults = dict(
            institution="MIT",
            degree="B.S.",
            field_of_study="Computer Science",
            start_date=date(2020, 9, 1),
        )
        defaults.update(overrides)
        return defaults

    def test_valid_current_no_end_date(self):
        edu = EducationBase(**self._base_kwargs(is_current=True, end_date=None))
        assert edu.is_current is True
        assert edu.end_date is None

    def test_valid_completed_with_end_date(self):
        edu = EducationBase(**self._base_kwargs(
            is_current=False,
            start_date=date(2018, 9, 1),
            end_date=date(2022, 5, 1),
        ))
        assert edu.end_date == date(2022, 5, 1)

    def test_valid_same_start_end_date(self):
        edu = EducationBase(**self._base_kwargs(
            start_date=date(2020, 6, 1),
            end_date=date(2020, 6, 1),
        ))
        assert edu.end_date == date(2020, 6, 1)

    def test_invalid_is_current_with_end_date(self):
        with pytest.raises(ValidationError) as exc_info:
            EducationBase(**self._base_kwargs(
                is_current=True,
                end_date=date(2024, 5, 1),
            ))
        assert "end_date must be null when is_current is True" in str(exc_info.value)

    def test_invalid_end_date_before_start_date(self):
        with pytest.raises(ValidationError) as exc_info:
            EducationBase(**self._base_kwargs(
                start_date=date(2022, 9, 1),
                end_date=date(2021, 5, 1),
            ))
        assert "end_date must be on or after start_date" in str(exc_info.value)

    def test_valid_no_end_date_not_current(self):
        # end_date=None + is_current=False is a valid in-progress state
        edu = EducationBase(**self._base_kwargs(is_current=False, end_date=None))
        assert edu.end_date is None

    def test_valid_gpa_bounds(self):
        edu = EducationBase(**self._base_kwargs(gpa=3.9))
        assert edu.gpa == pytest.approx(3.9)

    def test_invalid_gpa_above_max(self):
        with pytest.raises(ValidationError):
            EducationBase(**self._base_kwargs(gpa=4.1))

    def test_invalid_gpa_below_min(self):
        with pytest.raises(ValidationError):
            EducationBase(**self._base_kwargs(gpa=-0.1))


# ---------------------------------------------------------------------------
# EducationUpdate — partial-field timeline validation (update path)
# ---------------------------------------------------------------------------

class TestEducationUpdateValidation:
    def test_valid_set_is_current_true_no_end_date(self):
        upd = EducationUpdate(is_current=True, end_date=None)
        assert upd.is_current is True
        assert upd.end_date is None

    def test_invalid_is_current_true_with_end_date(self):
        with pytest.raises(ValidationError) as exc_info:
            EducationUpdate(is_current=True, end_date=date(2024, 5, 1))
        assert "end_date must be null when is_current is True" in str(exc_info.value)

    def test_invalid_end_date_before_start_date(self):
        with pytest.raises(ValidationError) as exc_info:
            EducationUpdate(start_date=date(2022, 9, 1), end_date=date(2021, 1, 1))
        assert "end_date must be on or after start_date" in str(exc_info.value)

    def test_valid_end_date_only_no_start_date_provided(self):
        # When only end_date is given (start_date comes from DB), no cross-check possible
        upd = EducationUpdate(end_date=date(2024, 5, 1))
        assert upd.end_date == date(2024, 5, 1)

    def test_valid_clear_end_date_when_switching_to_current(self):
        upd = EducationUpdate(is_current=True, end_date=None)
        assert upd.end_date is None
        assert upd.is_current is True

    def test_valid_partial_update_gpa_none(self):
        # Explicitly setting gpa=None should be accepted (clearing it)
        upd = EducationUpdate(gpa=None)
        assert upd.gpa is None

    def test_valid_partial_update_honors_none(self):
        upd = EducationUpdate(honors=None)
        assert upd.honors is None

    def test_valid_partial_update_activities_none(self):
        upd = EducationUpdate(activities=None)
        assert upd.activities is None

    def test_empty_update_is_valid(self):
        # All-None update is valid (noop); caller filters with exclude_unset
        upd = EducationUpdate()
        assert upd.model_fields_set == set()

    def test_valid_is_current_false_not_enforced(self):
        # is_current=False alone — no rule triggered
        upd = EducationUpdate(is_current=False)
        assert upd.is_current is False


# ---------------------------------------------------------------------------
# EducationRepository.update_education — None-value handling
# ---------------------------------------------------------------------------

class TestUpdateEducationRepository:
    def _make_repo(self, existing_record):
        """Build a repository whose .get() returns the given record."""
        db = MagicMock()
        repo = EducationRepository(db)
        repo.get = MagicMock(return_value=existing_record)
        repo.update = MagicMock(side_effect=lambda obj: obj)
        return repo

    def _fake_education(self, **kwargs):
        edu = MagicMock()
        edu.configure_mock(**kwargs)
        # Make hasattr return True for all attribute names we set
        for attr in kwargs:
            setattr(edu, attr, kwargs[attr])
        return edu

    def test_clears_gpa_when_set_to_none(self):
        edu = self._fake_education(id=1, gpa=3.5, honors="Dean's List")
        repo = self._make_repo(edu)

        result = repo.update_education(1, gpa=None)

        assert result.gpa is None

    def test_clears_honors_when_set_to_none(self):
        edu = self._fake_education(id=1, honors="Magna Cum Laude")
        repo = self._make_repo(edu)

        result = repo.update_education(1, honors=None)

        assert result.honors is None

    def test_clears_activities_when_set_to_none(self):
        edu = self._fake_education(id=1, activities="Chess Club")
        repo = self._make_repo(edu)

        result = repo.update_education(1, activities=None)

        assert result.activities is None

    def test_clears_end_date_when_switching_to_current(self):
        edu = self._fake_education(id=1, end_date=date(2022, 5, 1), is_current=False)
        repo = self._make_repo(edu)

        result = repo.update_education(1, end_date=None, is_current=True)

        assert result.end_date is None
        assert result.is_current is True

    def test_does_not_touch_unmentioned_fields(self):
        edu = self._fake_education(id=1, institution="MIT", degree="B.S.", gpa=3.9)
        repo = self._make_repo(edu)

        # Only update institution — gpa should stay 3.9
        repo.update_education(1, institution="Harvard")

        assert edu.institution == "Harvard"
        assert edu.gpa == 3.9

    def test_returns_none_when_not_found(self):
        db = MagicMock()
        repo = EducationRepository(db)
        repo.get = MagicMock(return_value=None)

        result = repo.update_education(999, gpa=None)

        assert result is None
