"""Education repository for database operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.orm.education import Education
from src.repositories.base import BaseRepository


class EducationRepository(BaseRepository[Education]):
    """Repository for education operations."""

    def __init__(self, db: Session):
        """Initialize education repository."""
        super().__init__(Education, db)

    def get_by_user(self, user_id: int) -> List[Education]:
        """Get all education entries for a user."""
        stmt = (
            select(Education)
            .where(Education.user_id == user_id)
            .order_by(Education.start_date.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create_education(
        self,
        user_id: int,
        institution: str,
        degree: str,
        field_of_study: str,
        start_date,
        end_date=None,
        is_current: bool = False,
        gpa: Optional[float] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        honors: Optional[str] = None,
        activities: Optional[str] = None,
    ) -> Education:
        """Create a new education entry."""
        education = Education(
            user_id=user_id,
            institution=institution,
            degree=degree,
            field_of_study=field_of_study,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            gpa=gpa,
            location=location,
            description=description,
            honors=honors,
            activities=activities,
        )
        return self.create(education)

    def update_education(
        self,
        education_id: int,
        **kwargs,
    ) -> Optional[Education]:
        """Update an existing education entry."""
        education = self.get(education_id)
        if not education:
            return None

        for key, value in kwargs.items():
            if hasattr(education, key) and value is not None:
                setattr(education, key, value)

        return self.update(education)

    def delete_by_user(self, user_id: int) -> int:
        """Delete all education entries for a user."""
        educations = self.get_by_user(user_id)
        count = len(educations)
        for edu in educations:
            self.db.delete(edu)
        self.db.commit()
        return count
