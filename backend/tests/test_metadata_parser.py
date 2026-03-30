import json
import os
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.core.detectors.metadata import (
    parse_metadata,
    save_metadata_json,
    should_skip_file,
)


class TestFixtures:
    """Group all test fixtures together for better organization."""

    @pytest.fixture
    def mock_cwd_outputs(self, tmp_path, monkeypatch):
        """Mock Path.cwd() to return test directory for outputs."""
        monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
        return tmp_path / "outputs"

    @pytest.fixture
    def sample_dataframe(self):
        """Create a standard test dataframe with Unix timestamps and new fields."""
        return pd.DataFrame(
            [
                {
                    "filename": "test1.txt",
                    "path": "test1.txt",
                    "file_type": "text/plain",
                    "language": "Text",
                    "file_size": 1024,
                    "lines_of_code": 50,
                    "created_timestamp": 1698342000.0,
                    "last_modified": 1698345600.0,
                    "status": "success",
                },
                {
                    "filename": "test2.py",
                    "path": "test2.py",
                    "file_type": "text/x-script.python",
                    "language": "Python",
                    "file_size": 2048,
                    "lines_of_code": 100,
                    "created_timestamp": 1698345600.0,
                    "last_modified": 1698349200.0,
                    "status": "success",
                },
            ]
        )

    @pytest.fixture
    def error_dataframe(self):
        """Create a dataframe with error records that match the expected format."""
        df = pd.DataFrame(
            [
                {
                    "filename": "good.txt",
                    "path": "good.txt",
                    "file_type": "text/plain",
                    "language": "Text",
                    "file_size": 512,
                    "lines_of_code": 25,
                    "created_timestamp": 1698342000.0,
                    "last_modified": 1698345600.0,
                    "status": "success",
                },
                {
                    "filename": "bad.txt",
                    "path": "bad.txt",
                    "file_type": "ERROR",
                    "language": "Unknown",
                    "file_size": None,
                    "lines_of_code": None,
                    "created_timestamp": None,
                    "last_modified": None,
                    "error": "Permission denied",
                    "status": "error",
                },
            ]
        )
        return df.where(df.notna(), None)

    @pytest.fixture
    def filtered_dataframe(self):
        """Create a dataframe with filtered records."""
        return pd.DataFrame(
            [
                {
                    "filename": "test.pyc",
                    "path": "test.pyc",
                    "file_type": "FILTERED",
                    "language": "Filtered",
                    "file_size": None,
                    "lines_of_code": None,
                    "created_timestamp": None,
                    "last_modified": None,
                    "skip_reason": "skipped extension: .pyc",
                    "status": "filtered",
                }
            ]
        )


class TestShouldSkipFile:
    """Test cases for should_skip_file function."""

    def test_skip_by_extension(self):
        """Test skipping files by extension."""
        should_skip, reason = should_skip_file("/path/test.pyc", "test.pyc")
        assert should_skip is True
        assert "skipped extension: .pyc" in reason

    def test_skip_by_filename(self):
        """Test skipping files by filename."""
        should_skip, reason = should_skip_file("/path/.DS_Store", ".DS_Store")
        assert should_skip is True
        assert "skipped filename: .DS_Store" in reason

    def test_skip_by_directory(self):
        """Test skipping files in excluded directories."""
        should_skip, reason = should_skip_file(
            "/path/__pycache__/module.py", "module.py"
        )
        assert should_skip is True
        assert "skipped directory: __pycache__" in reason

    def test_do_not_skip_valid_file(self):
        """Test not skipping valid files."""
        should_skip, reason = should_skip_file("/path/main.py", "main.py")
        assert should_skip is False
        assert reason == ""


class TestParseMetadata(TestFixtures):
    """Test cases for parse_metadata function."""

    @patch(
        "src.core.detectors.metadata.should_skip_file"
    )  # Mock the should_skip_file function
    @patch("src.core.detectors.metadata.FileAnalyzer")
    @patch("src.core.detectors.metadata.LanguageConfig")
    @patch("src.core.detectors.metadata.CommentDetector")
    @patch("src.core.detectors.metadata.FileWalker")
    @patch("src.core.detectors.metadata.magic")
    @patch("os.walk")
    @patch("os.path.getsize")
    @patch("os.path.getctime")
    @patch("os.path.getmtime")
    def test_returns_dataframe_with_new_fields(
        self,
        mock_getmtime,
        mock_getctime,
        mock_getsize,
        mock_walk,
        mock_magic,
        mock_file_walker,
        mock_comment_detector,
        mock_language_config,
        mock_file_analyzer,
        mock_should_skip,
    ):
        """Test that parse_metadata returns DataFrame with new language and LOC fields."""
        # Arrange
        mock_walk.return_value = [("/test", [], ["test.py", "test.txt"])]

        # Mock should_skip_file to return False (don't skip) for both files
        mock_should_skip.return_value = (False, "")

        mock_magic.from_file.side_effect = ["text/x-script.python", "text/plain"]
        mock_getsize.side_effect = [1024, 512]
        mock_getctime.side_effect = [1698342000.0, 1698345600.0]
        mock_getmtime.side_effect = [1698345600.0, 1698349200.0]

        # Mock language analyzer components
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.detect_language_by_extension.side_effect = [
            "Python",
            "Text",
        ]

        # Mock LOC analysis - return different values for each file
        mock_file_stats_py = MagicMock()
        mock_file_stats_py.code_lines = 50
        mock_file_stats_txt = MagicMock()
        mock_file_stats_txt.code_lines = 25
        mock_analyzer_instance.count_lines_of_code.side_effect = [
            mock_file_stats_py,
            mock_file_stats_txt,
        ]

        mock_file_analyzer.return_value = mock_analyzer_instance
        mock_language_config.return_value = MagicMock()
        mock_comment_detector.return_value = MagicMock()
        mock_file_walker.return_value = MagicMock()

        # Act
        result, project_root = parse_metadata("/test")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

        # Check that new fields are present
        expected_columns = {
            "filename",
            "path",
            "file_type",
            "language",
            "file_size",
            "lines_of_code",
            "created_timestamp",
            "last_modified",
            "status",
        }
        assert expected_columns.issubset(set(result.columns))

        # Check Python file
        python_file = result[result["filename"] == "test.py"].iloc[0]
        assert python_file["language"] == "Python"
        assert python_file["lines_of_code"] == 50
        assert python_file["status"] == "success"

        # Check text file
        text_file = result[result["filename"] == "test.txt"].iloc[0]
        assert text_file["language"] == "Text"
        assert text_file["lines_of_code"] == 25
        assert text_file["status"] == "success"

        # Verify should_skip_file was called for both files
        assert mock_should_skip.call_count == 2

    def test_empty_directory(self, tmp_path):
        """Test parse_metadata with empty directory."""
        # Arrange
        directory = tmp_path / "empty"
        directory.mkdir()

        # Act
        result, project_root = parse_metadata(str(directory))

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert result.empty
        assert isinstance(project_root, str)
        assert project_root == str(directory.resolve())


class TestSaveMetadataJson(TestFixtures):
    """Test cases for save_metadata_json function."""

    def test_creates_valid_json_structure_with_new_fields(
        self, mock_cwd_outputs, sample_dataframe
    ):
        """Test that save_metadata_json creates valid JSON with new fields."""
        # Act
        result_path = save_metadata_json(
            sample_dataframe, "test_output.json", "/tmp/test_project"
        )

        # Assert
        assert os.path.exists(result_path)

        with open(result_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Check top-level structure
        assert (
            "metadata" in json_data
            and "files" in json_data
            and "project_root" in json_data
        )

        # Check project_root field
        assert json_data["project_root"] == "/tmp/test_project"

        # Check metadata fields (updated for schema version 2.3)
        metadata = json_data["metadata"]
        assert metadata["total_files"] == 2
        assert metadata["successful_parses"] == 2
        assert metadata["failed_parses"] == 0
        assert metadata["filtered_files"] == 0
        assert metadata["schema_version"] == "2.3"  # Updated version
        assert metadata["total_size_bytes"] == 3072  # 1024 + 2048
        assert metadata["average_file_size_bytes"] == 1536.0

        # Check new LOC fields
        assert metadata["total_lines_of_code"] == 150  # 50 + 100
        assert metadata["average_lines_of_code"] == 75.0  # 150 / 2
        assert metadata["files_with_loc"] == 2

        # Check file details with new fields
        files = json_data["files"]
        python_file = next(f for f in files if f["filename"] == "test2.py")
        assert python_file["language"] == "Python"
        assert python_file["lines_of_code"] == 100
        assert python_file["status"] == "success"

    def test_handles_error_records_with_new_fields(
        self, mock_cwd_outputs, error_dataframe
    ):
        """Test handling of records with errors including new fields."""
        # Act
        result_path = save_metadata_json(
            error_dataframe, "error_test.json", "/tmp/error_project"
        )

        # Assert
        with open(result_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        metadata = json_data["metadata"]
        assert metadata["total_files"] == 2
        assert metadata["successful_parses"] == 1  # Only good.txt is successful
        assert metadata["failed_parses"] == 1  # bad.txt is error
        assert metadata["filtered_files"] == 0

        # LOC stats should only count successful files
        assert metadata["total_lines_of_code"] == 25  # Only good.txt
        assert metadata["average_lines_of_code"] == 25.0
        assert metadata["files_with_loc"] == 1

        files = json_data["files"]
        bad_file = next(f for f in files if f["filename"] == "bad.txt")
        good_file = next(f for f in files if f["filename"] == "good.txt")

        # Check good file
        assert good_file["language"] == "Text"
        assert good_file["lines_of_code"] == 25
        assert good_file["status"] == "success"

        # Check bad file
        assert bad_file["language"] == "Unknown"
        assert bad_file["lines_of_code"] is None
        assert bad_file["status"] == "error"
        assert "error" in bad_file
        assert bad_file["error"] == "Permission denied"

    def test_handles_filtered_records(self, mock_cwd_outputs, filtered_dataframe):
        """Test handling of filtered records."""
        # Act
        result_path = save_metadata_json(
            filtered_dataframe, "filtered_test.json", "/tmp/filtered_project"
        )

        # Assert
        with open(result_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        metadata = json_data["metadata"]
        assert metadata["total_files"] == 1
        assert metadata["successful_parses"] == 0
        assert metadata["failed_parses"] == 0
        assert metadata["filtered_files"] == 1

        # No LOC stats for filtered files
        assert metadata["total_lines_of_code"] == 0
        assert metadata["average_lines_of_code"] == 0
        assert metadata["files_with_loc"] == 0

        files = json_data["files"]
        filtered_file = files[0]
        assert filtered_file["language"] == "Filtered"
        assert filtered_file["lines_of_code"] is None
        assert filtered_file["status"] == "filtered"
        assert "skip_reason" in filtered_file
        assert filtered_file["skip_reason"] == "skipped extension: .pyc"

    def test_saves_to_outputs_directory_at_cwd(
        self, mock_cwd_outputs, sample_dataframe
    ):
        """Test that files are saved to outputs directory at current working directory."""
        # Act
        result_path = save_metadata_json(
            sample_dataframe, "cwd_test.json", "/tmp/cwd_project"
        )

        # Assert
        expected_path = mock_cwd_outputs / "cwd_test.json"
        assert result_path == str(expected_path)
        assert os.path.exists(result_path)

        # Verify outputs directory was created
        assert mock_cwd_outputs.exists()

    def test_handles_null_loc_values(self, mock_cwd_outputs):
        """Test handling of null/None LOC values."""
        # Arrange
        mixed_loc_data = pd.DataFrame(
            [
                {
                    "filename": "with_loc.py",
                    "path": "with_loc.py",
                    "file_type": "text/x-script.python",
                    "language": "Python",
                    "file_size": 1000,
                    "lines_of_code": 50,
                    "created_timestamp": 1698342000.0,
                    "last_modified": 1698345600.0,
                    "status": "success",
                },
                {
                    "filename": "without_loc.bin",
                    "path": "without_loc.bin",
                    "file_type": "application/octet-stream",
                    "language": "Unknown",
                    "file_size": 500,
                    "lines_of_code": None,
                    "created_timestamp": 1698342000.0,
                    "last_modified": 1698345600.0,
                    "status": "success",
                },
            ]
        )

        # Act
        result_path = save_metadata_json(
            mixed_loc_data, "mixed_loc_test.json", "/tmp/mixed_loc_project"
        )

        # Assert
        with open(result_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        metadata = json_data["metadata"]
        assert metadata["total_lines_of_code"] == 50  # Only count non-null LOC
        assert metadata["average_lines_of_code"] == 50.0  # 50 / 1
        assert metadata["files_with_loc"] == 1  # Only one file had LOC

        files = json_data["files"]
        with_loc = next(f for f in files if f["filename"] == "with_loc.py")
        without_loc = next(f for f in files if f["filename"] == "without_loc.bin")

        assert with_loc["lines_of_code"] == 50
        assert without_loc["lines_of_code"] is None

    def test_utf8_encoding_with_new_fields(self, mock_cwd_outputs):
        """Test UTF-8 character handling with new fields."""
        # Arrange
        unicode_data = pd.DataFrame(
            [
                {
                    "filename": "файл.py",
                    "path": "файл.py",
                    "file_type": "text/x-script.python",
                    "language": "Python",
                    "file_size": 300,
                    "lines_of_code": 15,
                    "created_timestamp": 1698342000.0,
                    "last_modified": 1698345600.0,
                    "status": "success",
                }
            ]
        )

        # Act
        result_path = save_metadata_json(
            unicode_data, "utf8_test.json", "/tmp/unicode_project"
        )

        # Assert
        with open(result_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        file_data = json_data["files"][0]
        assert file_data["filename"] == "файл.py"
        assert file_data["language"] == "Python"
        assert file_data["lines_of_code"] == 15
        assert file_data["status"] == "success"


class TestErrorHandling(TestFixtures):
    """Test error handling scenarios."""

    def test_file_write_permission_error(self, mock_cwd_outputs, sample_dataframe):
        """Test handling of file write permission errors."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError, match="Permission denied"):
                save_metadata_json(
                    sample_dataframe,
                    "write_error_test.json",
                    "/tmp/write_error_project",
                )

    def test_json_serialization_error(self, mock_cwd_outputs, sample_dataframe):
        """Test handling of JSON serialization errors."""
        with patch(
            "json.dump", side_effect=TypeError("Object is not JSON serializable")
        ):
            with pytest.raises(TypeError, match="Object is not JSON serializable"):
                save_metadata_json(
                    sample_dataframe, "json_error_test.json", "/tmp/json_error_project"
                )


class TestEdgeCases(TestFixtures):
    """Test edge cases and boundary conditions."""

    @pytest.mark.parametrize(
        "file_sizes,loc_values,expected_avg_size,expected_avg_loc",
        [
            ([0, 0], [0, 0], 0.0, 0.0),
            ([1000], [50], 1000.0, 50.0),
            ([1000, 2000], [50, 100], 1500.0, 75.0),
            ([1000, 2000], [50, None], 1500.0, 50.0),  # One null LOC
        ],
    )
    def test_statistics_edge_cases(
        self,
        mock_cwd_outputs,
        file_sizes,
        loc_values,
        expected_avg_size,
        expected_avg_loc,
    ):
        """Test statistics calculation edge cases with new LOC fields."""
        # Arrange
        data = pd.DataFrame(
            [
                {
                    "filename": f"file{i}.txt",
                    "path": f"file{i}.txt",
                    "file_type": "text/plain",
                    "language": "Text",
                    "file_size": size,
                    "lines_of_code": loc,
                    "created_timestamp": 1698342000.0,
                    "last_modified": 1698345600.0,
                    "status": "success",
                }
                for i, (size, loc) in enumerate(zip(file_sizes, loc_values))
            ]
        )

        # Act
        result_path = save_metadata_json(
            data, f"edge_case_test_{len(file_sizes)}.json", "/tmp/edge_case_project"
        )

        # Assert
        with open(result_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        metadata = json_data["metadata"]
        assert metadata["average_file_size_bytes"] == expected_avg_size
        assert metadata["total_size_bytes"] == sum(file_sizes)
        assert metadata["average_lines_of_code"] == expected_avg_loc

        # Count non-null LOC values
        non_null_loc = [loc for loc in loc_values if loc is not None]
        assert (
            metadata["total_lines_of_code"] == sum(non_null_loc) if non_null_loc else 0
        )
        assert metadata["files_with_loc"] == len(non_null_loc)
