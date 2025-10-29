import pandas as po
import pytest

from src.core.metadata_parser import parse_metadata


@pytest.fixture
def test_parse_metadata_returns_dataframe(temp):
    # Create a test directory and files
    directory = temp + "/data"
    directory.mkdir()
    file_1 = (directory + "/file1.txt").write_text("Chicken time!")
    file_2 = (directory + "/file2.log").write_text("Chicken log!")

    dataframe = parse_metadata(directory)

    # Check type
    assert isinstance(dataframe, po.DataFrame)

    # Check if dataframe has both files
    assert len(dataframe) == 2

    # Check if the columns exist
    expected_columns = {
        "filename",
        "path",
        "file_type",
        "file_size",
        "created_timestamp",
        "last_modified",
    }
    assert expected_columns.issubset(dataframe.columns)


def test_parse_metadata_empty_directory(tmp_path):
    directory = tmp_path / "empty"
    directory.mkdir()

    dataframe = parse_metadata(str(directory))
    assert isinstance(dataframe, po.DataFrame)
    assert dataframe.empty


def test_parse_metadata_returns_correct_paths(tmp_path):
    directory = tmp_path / "verify"
    directory.mkdir()

    file_path = directory / "sample.txt"
    file_path.write_text("Hello!")

    dataframe = parse_metadata(str(directory))

    row = dataframe.iloc[0]
    assert row["filename"] == "sample.txt"
    assert str(file_path) in row["path"]
