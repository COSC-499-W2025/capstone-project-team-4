"""Portfolio repository for database operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.orm.portfolio import Portfolio
from src.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    """Repository for portfolio operations."""

    def __init__(self, db: Session):
        """Initialize portfolio repository."""
        super().__init__(Portfolio, db)

    def get_by_user_id(self, user_id: int) -> Optional[Portfolio]:
        """Get portfolio by user ID."""
        stmt = select(Portfolio).where(Portfolio.user_id == user_id)
        return self.db.scalar(stmt)
