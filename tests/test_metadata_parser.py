import json
import os
import pandas as po
import pytest
from datetime import datetime
from pathlib import Path


from src.core.metadata_parser import parse_metadata, save_metadata_json


def test_parse_metadata_returns_dataframe(tmp_path):
    # Create a test directory and files
    directory = tmp_path / "data"
    directory.mkdir()
    file_1 = directory / "file1.txt"
    file_1.write_text("Chicken time!")
    file_2 = directory / "file2.log"
    file_2.write_text("Chicken log!")

    dataframe = parse_metadata(str(directory))

    # Check type
    assert isinstance(dataframe, po.DataFrame)

    # Check if dataframe has both files
    assert len(dataframe) == 2

    # Check if the columns exist
    expected_columns = {"filename", "path", "file_type", "last_modified"}
    assert expected_columns.issubset(dataframe.columns)



#  Tests for save_metadata_json
# These tests ensure that save_metadata_json correctly converts
# a metadata dataframe to JSON format and handles various scenarios.
def test_save_metadata_json_creates_valid_json(tmp_path, monkeypatch):
    """Test that save_metadata_json creates a valid JSON file with correct structure."""
    # Setup
    setup_test_environment(tmp_path, monkeypatch)
    dataframe = po.DataFrame(create_valid_metadata_records())
    
    # Execute
    result_path = save_metadata_json(dataframe, "test_output.json")
    
    # Verify
    assert os.path.exists(result_path)
    
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Assert structure and counts
    files = assert_json_structure(json_data, expected_total_files=2, expected_success=2, expected_failures=0)
    
    # Check specific file details
    file1 = files[0]
    assert file1["filename"] == "test1.txt"
    assert file1["path"] == "/tmp/test1.txt"
    assert file1["file_type"] == "ASCII text"
    assert file1["status"] == "success"
    assert "last_modified" in file1
    # Check timestamp format (timezone-agnostic)
    assert file1["last_modified"].startswith("2023-10-26T")
    assert len(file1["last_modified"]) == 19  # ISO format length
    
    
def test_save_metadata_json_handles_error_records(tmp_path, monkeypatch):
    """Test that save_metadata_json correctly handles records with errors."""
    # Setup
    setup_test_environment(tmp_path, monkeypatch)
    dataframe = po.DataFrame(create_error_metadata_records())
    
    # Execute
    result_path = save_metadata_json(dataframe, "error_test.json")
    
    # Verify
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Assert structure and counts
    files = assert_json_structure(json_data, expected_total_files=2, expected_success=1, expected_failures=1)
    
    # Check specific records
    error_file = next(f for f in files if f["filename"] == "bad.txt")
    success_file = next(f for f in files if f["filename"] == "good.txt")
    
    # Verify error record
    assert error_file["status"] == "error"
    assert error_file["error"] == "Permission denied"
    assert error_file["last_modified"] is None
    
    # Verify success record
    assert success_file["status"] == "success"
    assert "error" not in success_file


def test_save_metadata_json_handles_invalid_timestamps(tmp_path, monkeypatch):
    """Test that save_metadata_json handles invalid timestamps gracefully."""
    # Setup
    setup_test_environment(tmp_path, monkeypatch)
    dataframe = po.DataFrame(create_timestamp_test_records())
    
    # Execute
    result_path = save_metadata_json(dataframe, "timestamp_test.json")
    
    # Verify
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    files = json_data["files"]
    invalid_time_file = next(f for f in files if f["filename"] == "invalid_time.txt")
    no_time_file = next(f for f in files if f["filename"] == "no_time.txt")
    
    # Verify timestamp handling
    assert invalid_time_file["last_modified"] == "1969-12-31T23:59:59"  # -1 timestamp
    assert no_time_file["last_modified"] is None  # None timestamp


def test_save_metadata_json_custom_filename(tmp_path, monkeypatch):
    """Test that save_metadata_json uses custom filename correctly."""
    # Setup
    setup_test_environment(tmp_path, monkeypatch)
    test_data = [{"filename": "test.txt", "path": "/tmp/test.txt", "file_type": "text", "last_modified": None}]
    dataframe = po.DataFrame(test_data)
    
    # Execute
    custom_filename = "my_custom_output.json"
    result_path = save_metadata_json(dataframe, custom_filename)
    
    # Verify
    assert custom_filename in result_path
    assert os.path.exists(result_path)


def test_save_metadata_json_creates_outputs_directory(tmp_path, monkeypatch):
    """Test that save_metadata_json creates outputs directory if it doesn't exist."""
    # Setup
    setup_test_environment(tmp_path, monkeypatch)
    test_data = [{"filename": "test.txt", "path": "/tmp/test.txt", "file_type": "text", "last_modified": None}]
    dataframe = po.DataFrame(test_data)
    
    # Verify initial state
    outputs_dir = tmp_path / "src" / "outputs"
    assert not outputs_dir.exists()
    
    # Execute
    result_path = save_metadata_json(dataframe, "directory_test.json")
    
    # Verify
    assert outputs_dir.exists()
    assert outputs_dir.is_dir()


def test_save_metadata_json_utf8_encoding(tmp_path, monkeypatch):
    """Test that save_metadata_json handles UTF-8 characters correctly."""
    # Setup
    setup_test_environment(tmp_path, monkeypatch)
    dataframe = po.DataFrame(create_unicode_metadata_records())
    
    # Execute
    result_path = save_metadata_json(dataframe, "utf8_test.json")
    
    # Verify
    with open(result_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    files = json_data["files"]
    assert files[0]["filename"] == "файл.txt"
    assert files[0]["path"] == "/tmp/файл.txt"

#  Error handling tests
# These tests ensure that save_metadata_json properly handles various error scenarios.
def test_save_metadata_json_handles_file_write_error(tmp_path, monkeypatch):
    """Test that save_metadata_json properly handles file writing errors."""
    # Setup
    setup_test_environment(tmp_path, monkeypatch)
    dataframe = po.DataFrame(create_valid_metadata_records())
    
    # Mock the open function to raise an exception
    import builtins
    original_open = builtins.open
    
    def mock_open(*args, **kwargs):
        # Check if it's trying to write to our JSON file
        if len(args) > 0 and str(args[0]).endswith("write_error_test.json"):
            raise PermissionError("Permission denied: Cannot write to file")
        return original_open(*args, **kwargs)
    
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Execute and verify exception is raised
    with pytest.raises(PermissionError, match="Permission denied: Cannot write to file"):
        save_metadata_json(dataframe, "write_error_test.json")


def test_save_metadata_json_handles_json_serialization_error(tmp_path, monkeypatch):
    """Test that save_metadata_json handles JSON serialization errors."""
    # Setup
    setup_test_environment(tmp_path, monkeypatch)
    
    # Create dataframe with data that could cause JSON serialization issues
    # (though this is harder to trigger with our current data structure)
    dataframe = po.DataFrame(create_valid_metadata_records())
    
    # Mock json.dump to raise an exception
    import json as json_module
    original_dump = json_module.dump
    
    def mock_dump(*args, **kwargs):
        raise TypeError("Object is not JSON serializable")
    
    monkeypatch.setattr("json.dump", mock_dump)
    
    # Execute and verify exception is raised
    with pytest.raises(TypeError, match="Object is not JSON serializable"):
        save_metadata_json(dataframe, "json_error_test.json")


def test_save_metadata_json_handles_directory_creation_error(tmp_path, monkeypatch):
    """Test that save_metadata_json handles directory creation errors."""
    # Setup - but don't create the directory structure
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    mock_file_path = src_dir / "metadata_parser.py"
    monkeypatch.setattr("src.core.metadata_parser.__file__", str(mock_file_path))
    
    dataframe = po.DataFrame(create_valid_metadata_records())
    
    # Mock mkdir to raise an exception
    from pathlib import Path
    original_mkdir = Path.mkdir
    
    def mock_mkdir(self, mode=0o777, parents=False, exist_ok=False):
        if "outputs" in str(self):
            raise OSError("Permission denied: Cannot create directory")
        return original_mkdir(self, mode, parents, exist_ok)
    
    monkeypatch.setattr("pathlib.Path.mkdir", mock_mkdir)
    
    # Execute and verify exception is raised
    with pytest.raises(OSError, match="Permission denied: Cannot create directory"):
        save_metadata_json(dataframe, "dir_error_test.json")


# Test data fixtures
# These create sample dataframes to be used in tests
def create_valid_metadata_records():
    """Create sample metadata records for testing."""
    return [
        {
            "filename": "test1.txt",
            "path": "/tmp/test1.txt",
            "file_type": "ASCII text",
            "last_modified": 1698345600.0  # 2023-10-26 12:00:00
        },
        {
            "filename": "test2.jpg",
            "path": "/tmp/test2.jpg", 
            "file_type": "JPEG image data",
            "last_modified": 1698349200.0  # 2023-10-26 13:00:00
        }
    ]


def create_error_metadata_records():
    """Create metadata records with success and error cases."""
    return [
        {
            "filename": "good.txt",
            "path": "/tmp/good.txt",
            "file_type": "ASCII text",
            "last_modified": 1698345600.0,
            "error": None  # Explicitly set None to avoid pandas NaN
        },
        {
            "filename": "bad.txt",
            "path": "/tmp/bad.txt",
            "file_type": "ERROR",
            "last_modified": None,
            "error": "Permission denied"
        }
    ]


def create_timestamp_test_records():
    """Create metadata records with invalid timestamps."""
    return [
        {
            "filename": "invalid_time.txt",
            "path": "/tmp/invalid_time.txt",
            "file_type": "ASCII text",
            "last_modified": -1  # Invalid timestamp
        },
        {
            "filename": "no_time.txt", 
            "path": "/tmp/no_time.txt",
            "file_type": "ASCII text",
            "last_modified": None
        }
    ]


def create_unicode_metadata_records():
    """Create metadata records with Unicode characters."""
    return [
        {
            "filename": "файл.txt",  # Cyrillic filename
            "path": "/tmp/файл.txt",
            "file_type": "UTF-8 Unicode text",
            "last_modified": 1698345600.0
        }
    ]


def setup_test_environment(tmp_path, monkeypatch):
    """Setup common test environment with mocked file paths."""
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    mock_file_path = src_dir / "metadata_parser.py"
    monkeypatch.setattr("src.core.metadata_parser.__file__", str(mock_file_path))
    return src_dir


def assert_json_structure(json_data, expected_total_files, expected_success, expected_failures):
    """Assert that JSON has the expected structure and counts."""
    # Check top-level structure
    assert "metadata" in json_data
    assert "files" in json_data
    
    # Check metadata section
    metadata = json_data["metadata"]
    required_fields = {"generated_at", "total_files", "successful_parses", "failed_parses", "schema_version"}
    assert all(field in metadata for field in required_fields)
    
    assert metadata["total_files"] == expected_total_files
    assert metadata["successful_parses"] == expected_success
    assert metadata["failed_parses"] == expected_failures
    assert metadata["schema_version"] == "1.0"
    
    # Check files section
    files = json_data["files"]
    assert len(files) == expected_total_files
    return files
