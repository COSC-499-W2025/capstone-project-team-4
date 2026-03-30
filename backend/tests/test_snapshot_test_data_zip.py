import zipfile
from pathlib import Path


def test_snapshot_test_data_zip_contains_required_projects():
    zip_path = Path(__file__).resolve().parent / "test-data" / "test-data.zip"
    assert zip_path.exists(), f"Missing test data zip: {zip_path}"

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())

    required_prefixes = [
        "code_indiv_proj/",
        "code_collab_proj/",
        "text_indiv_proj/",
        "image_indiv_proj/",
    ]

    for prefix in required_prefixes:
        assert any(name.startswith(prefix) for name in names), (
            f"Missing required folder in zip: {prefix}"
        )
