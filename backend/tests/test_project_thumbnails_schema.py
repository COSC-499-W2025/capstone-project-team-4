from datetime import datetime

from src.models.database import Base
from src.models.orm.project import Project
from src.models.schemas.project import ProjectSummary


def test_project_thumbnail_schema_contract():
    import src.models.orm  # noqa: F401

    # model/table registered with SQLAlchemy metadata
    assert "project_thumbnails" in Base.metadata.tables

    # Project has a 1:1 relationship named "thumbnail"
    rel = Project.__mapper__.relationships.get("thumbnail")
    assert rel is not None
    assert rel.uselist is False
    assert rel.mapper.class_.__name__ == "ProjectThumbnail"

    # Pydantic schema exposes thumbnail metadata fields
    now = datetime.utcnow()
    p = ProjectSummary(
        id=1,
        name="demo",
        source_type="local",
        created_at=now,
        has_thumbnail=True,
        thumbnail_updated_at=now,
        thumbnail_endpoint="/api/projects/1/thumbnail",
    )
    assert p.has_thumbnail is True
    assert p.thumbnail_updated_at == now
    assert p.thumbnail_endpoint == "/api/projects/1/thumbnail"