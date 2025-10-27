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
    expected_columns = {"filename", "path", "file_type", "last_modified"}
    assert expected_columns.issubset(dataframe.columns)
