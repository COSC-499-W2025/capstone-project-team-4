"""ContributorCommit ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.orm.contributor import Contributor


class ContributorCommit(Base):
    """Model for individual commits by contributors."""

    __tablename__ = "contributor_commits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    contributor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contributors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_hash: Mapped[str] = mapped_column(String(40), nullable=False)
    commit_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    author_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    commit_message: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    contributor: Mapped["Contributor"] = relationship(
        "Contributor", back_populates="commit_history"
    )
