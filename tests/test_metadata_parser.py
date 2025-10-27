import json
import os
import pandas as po
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open

from src.core.metadata_parser import parse_metadata, save_metadata_json


# Fixtures for common test setup
# These create sample dataframes to be used in tests
@pytest.fixture
def mock_metadata_parser_path(tmp_path, monkeypatch):
    """Setup mock file path for metadata_parser module."""
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    mock_file_path = src_dir / "metadata_parser.py"
    monkeypatch.setattr("src.core.metadata_parser.__file__", str(mock_file_path))
    return src_dir

@pytest.fixture
def sample_dataframe():
    """Create a standard test dataframe with datetime objects (as parse_metadata returns)."""
    return po.DataFrame([
        {
            "filename": "test1.txt",
            "path": "/tmp/test1.txt",
            "file_type": "text/plain",
            "last_modified": datetime.fromtimestamp(1698345600.0)  # datetime object
        },
        {
            "filename": "test2.jpg",
            "path": "/tmp/test2.jpg", 
            "file_type": "image/jpeg",
            "last_modified": datetime.fromtimestamp(1698349200.0)  # datetime object
        }
    ])

@pytest.fixture
def error_dataframe():
    """Create a dataframe with error records."""
    return po.DataFrame([
        {
            "filename": "good.txt",
            "path": "/tmp/good.txt",
            "file_type": "text/plain",
            "last_modified": datetime.fromtimestamp(1698345600.0),  # datetime object
            "error": None
        },
        {
            "filename": "bad.txt",
            "path": "/tmp/bad.txt",
            "file_type": "ERROR",
            "last_modified": None,
            "error": "Permission denied"
        }
    ])


# Parse metadata tests
def test_parse_metadata_returns_dataframe(tmp_path):
    """Test that parse_metadata returns a proper DataFrame."""
    # Create test directory and files
    directory = tmp_path / "data"
    directory.mkdir()
    (directory / "file1.txt").write_text("Chicken time!")
    (directory / "file2.log").write_text("Chicken log!")

    dataframe = parse_metadata(str(directory))

    assert isinstance(dataframe, po.DataFrame)
    assert len(dataframe) == 2
    expected_columns = {"filename", "path", "file_type", "last_modified"}
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


# Save metadata JSON tests
def test_save_metadata_json_creates_valid_json(mock_metadata_parser_path, sample_dataframe):
    """Test that save_metadata_json creates a valid JSON file with correct structure."""
    result_path = save_metadata_json(sample_dataframe, "test_output.json")
    
    assert os.path.exists(result_path)
    
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Check structure
    assert "metadata" in json_data and "files" in json_data
    assert json_data["metadata"]["total_files"] == 2
    assert json_data["metadata"]["successful_parses"] == 2
    assert json_data["metadata"]["failed_parses"] == 0
    assert json_data["metadata"]["schema_version"] == "1.0"
    
    # Check file details - now expecting Unix timestamps
    files = json_data["files"]
    assert files[0]["filename"] == "test1.txt"
    assert files[0]["status"] == "success"
    assert files[0]["last_modified"] == 1698345600.0  # Unix timestamp, not ISO string
    assert files[1]["last_modified"] == 1698349200.0  # Unix timestamp
    
    
def test_save_metadata_json_handles_error_records(mock_metadata_parser_path, error_dataframe):
    """Test that save_metadata_json correctly handles records with errors."""
    result_path = save_metadata_json(error_dataframe, "error_test.json")
    
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Check counts
    assert json_data["metadata"]["total_files"] == 2
    assert json_data["metadata"]["successful_parses"] == 1
    assert json_data["metadata"]["failed_parses"] == 1
    
    # Check specific records
    files = json_data["files"]
    error_file = next(f for f in files if f["filename"] == "bad.txt")
    success_file = next(f for f in files if f["filename"] == "good.txt")
    
    assert error_file["status"] == "error"
    assert error_file["error"] == "Permission denied"
    assert error_file["last_modified"] is None  # None for error records
    assert success_file["status"] == "success"
    assert success_file["last_modified"] == 1698345600.0  # Unix timestamp


def test_save_metadata_json_handles_invalid_timestamps(mock_metadata_parser_path):
    """Test that save_metadata_json handles invalid timestamps gracefully."""
    timestamp_data = po.DataFrame([
        {
            "filename": "invalid_time.txt", 
            "path": "/tmp/invalid_time.txt", 
            "file_type": "text/plain", 
            "last_modified": datetime.fromtimestamp(-1)  # Invalid but convertible datetime
        },
        {
            "filename": "no_time.txt", 
            "path": "/tmp/no_time.txt", 
            "file_type": "text/plain", 
            "last_modified": None
        }
    ])
    
    result_path = save_metadata_json(timestamp_data, "timestamp_test.json")
    
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    files = json_data["files"]
    invalid_time_file = next(f for f in files if f["filename"] == "invalid_time.txt")
    no_time_file = next(f for f in files if f["filename"] == "no_time.txt")
    
    assert invalid_time_file["last_modified"] == -1.0  # Unix timestamp
    assert no_time_file["last_modified"] is None


def test_save_metadata_json_custom_filename(mock_metadata_parser_path, sample_dataframe):
    """Test that save_metadata_json uses custom filename correctly."""
    custom_filename = "my_custom_output.json"
    result_path = save_metadata_json(sample_dataframe, custom_filename)
    
    assert custom_filename in result_path
    assert os.path.exists(result_path)


def test_save_metadata_json_creates_outputs_directory(tmp_path, monkeypatch, sample_dataframe):
    """Test that save_metadata_json creates outputs directory if it doesn't exist."""
    # Setup without creating outputs directory
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    mock_file_path = src_dir / "metadata_parser.py"
    monkeypatch.setattr("src.core.metadata_parser.__file__", str(mock_file_path))
    
    outputs_dir = tmp_path / "src" / "outputs"
    assert not outputs_dir.exists()
    
    result_path = save_metadata_json(sample_dataframe, "directory_test.json")
    
    assert outputs_dir.exists()


def test_save_metadata_json_utf8_encoding(mock_metadata_parser_path):
    """Test that save_metadata_json handles UTF-8 characters correctly."""
    unicode_data = po.DataFrame([{
        "filename": "файл.txt",
        "path": "/tmp/файл.txt",
        "file_type": "text/plain",
        "last_modified": datetime.fromtimestamp(1698345600.0)  # datetime object
    }])
    
    result_path = save_metadata_json(unicode_data, "utf8_test.json")
    
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    assert json_data["files"][0]["filename"] == "файл.txt"
    assert json_data["files"][0]["last_modified"] == 1698345600.0  # Unix timestamp


def test_save_metadata_json_handles_unix_timestamps_input(mock_metadata_parser_path):
    """Test that save_metadata_json can handle Unix timestamps as input."""
    unix_timestamp_data = po.DataFrame([{
        "filename": "unix_time.txt",
        "path": "/tmp/unix_time.txt",
        "file_type": "text/plain",
        "last_modified": 1698345600.0  # Already Unix timestamp
    }])
    
    result_path = save_metadata_json(unix_timestamp_data, "unix_test.json")
    
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    assert json_data["files"][0]["last_modified"] == 1698345600.0


def test_save_metadata_json_metadata_timestamp_is_unix(mock_metadata_parser_path, sample_dataframe):
    """Test that the metadata generated_at field uses Unix timestamp."""
    result_path = save_metadata_json(sample_dataframe, "metadata_time_test.json")
    
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Check that generated_at is a Unix timestamp (number, not string)
    generated_at = json_data["metadata"]["generated_at"]
    assert isinstance(generated_at, (int, float))
    
    # Should be close to current time (within 1 minute)
    current_time = datetime.now().timestamp()
    assert abs(generated_at - current_time) < 60


# Error handling tests
def test_save_metadata_json_handles_file_write_error(mock_metadata_parser_path, sample_dataframe):
    """Test that save_metadata_json properly handles file writing errors."""
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError, match="Permission denied"):
            save_metadata_json(sample_dataframe, "write_error_test.json")


def test_save_metadata_json_handles_json_serialization_error(mock_metadata_parser_path, sample_dataframe):
    """Test that save_metadata_json handles JSON serialization errors."""
    with patch("json.dump", side_effect=TypeError("Object is not JSON serializable")):
        with pytest.raises(TypeError, match="Object is not JSON serializable"):
            save_metadata_json(sample_dataframe, "json_error_test.json")


def test_save_metadata_json_handles_directory_creation_error(mock_metadata_parser_path, sample_dataframe):
    """Test that save_metadata_json handles directory creation errors."""
    with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
        with pytest.raises(OSError, match="Permission denied"):
            save_metadata_json(sample_dataframe, "dir_error_test.json")




