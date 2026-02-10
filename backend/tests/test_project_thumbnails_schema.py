from src.models.database import Base


def test_project_thumbnails_table_registered_in_metadata():
    import src.models.orm  # noqa: F401

    assert "project_thumbnails" in Base.metadata.tables
