"""
File metadata extraction module.

This module provides functionality to parse file metadata from projects,
including file types, sizes, timestamps, and lines of code.

Migrated from src/core/metadata_parser.py
Updated to use unified constants from src/core/constants.py
"""

import json
import logging
import mimetypes
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime
from pathlib import Path
from typing import Tuple

import magic
import pandas as pd
from tqdm import tqdm

from src.core.constants import (
    SKIP_DIRECTORIES,
    SKIP_EXTENSIONS,
    SKIP_FILENAMES,
    MAX_FILE_SIZE,
    MIN_FILE_SIZE,
)
from src.core.analyzers.language import (
    LanguageConfig,
    FileAnalyzer,
    CommentDetector,
    FileWalker,
)

logger = logging.getLogger(__name__)

# Timeout for magic.from_file() calls (in seconds)
MAGIC_TIMEOUT_SECONDS = 5


# =============================================================================
# Safe file type detection
# =============================================================================


def _get_file_type_with_magic(file_path: str) -> str:
    """Call magic.from_file() - used internally with timeout wrapper."""
    return magic.from_file(file_path, mime=True)


def get_file_type_safe(file_path: str, timeout: float = MAGIC_TIMEOUT_SECONDS) -> str:
    """
    Safely detect file MIME type with timeout and fallback.

    Uses python-magic with a timeout wrapper. Falls back to mimetypes
    module if magic hangs or fails.

    Args:
        file_path: Path to the file
        timeout: Maximum seconds to wait for magic detection

    Returns:
        MIME type string (e.g., "text/plain", "application/octet-stream")
    """
    # Try magic with timeout
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_get_file_type_with_magic, file_path)
            file_type = future.result(timeout=timeout)
            return file_type
    except FuturesTimeoutError:
        logger.warning("magic.from_file() timed out for %s, using fallback", file_path)
    except Exception as e:
        logger.warning("magic.from_file() failed for %s: %s, using fallback", file_path, e)

    # Fallback to mimetypes module
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return mime_type
    except Exception as e:
        logger.warning("mimetypes.guess_type() failed for %s: %s", file_path, e)

    # Final fallback
    return "application/octet-stream"


# =============================================================================
# File filtering
# =============================================================================


def should_skip_file(file_path: str, file_name: str) -> Tuple[bool, str]:
    """
    Determines if a file should be skipped based on filtering rules.

    Args:
        file_path: Full path to the file
        file_name: Just the filename

    Returns:
        tuple: (should_skip: bool, reason: str)
    """
    path_obj = Path(file_path)

    # Check file extension
    if path_obj.suffix.lower() in SKIP_EXTENSIONS:
        return True, f"skipped extension: {path_obj.suffix}"

    # Check filename
    if file_name in SKIP_FILENAMES:
        return True, f"skipped filename: {file_name}"

    # Check if file is in a skipped directory
    parts = path_obj.parts
    for part in parts:
        if part in SKIP_DIRECTORIES:
            return True, f"skipped directory: {part}"

    # Check for patterns in path
    path_str = str(path_obj).lower()
    for skip_pattern in SKIP_DIRECTORIES:
        if skip_pattern.startswith("*") and skip_pattern.endswith("*"):
            # Pattern like "*debug*"
            pattern = skip_pattern.strip("*")
            if pattern in path_str:
                return True, f"skipped pattern: {skip_pattern}"
        elif skip_pattern.startswith("*"):
            # Pattern like "*.log"
            if path_str.endswith(skip_pattern[1:]):
                return True, f"skipped pattern: {skip_pattern}"

    # Check file size
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            return True, f"file too large: {file_size} bytes"
        if file_size < MIN_FILE_SIZE:
            return True, f"file too small: {file_size} bytes"
    except OSError:
        # If we can't get file size, let it through for now
        pass

    return False, ""


# =============================================================================
# Metadata parsing
# =============================================================================


def parse_metadata(
    folder_path: str = "", include_filtered: bool = False
) -> Tuple[pd.DataFrame, str]:
    """
    Opens up a folder from a recently extracted zip file and lists the file type,
    file size, and created/modified timestamps.

    Args:
        folder_path: the path to the directory/folder to be parsed (default "")
        include_filtered: if True, includes filtered files with their skip reason (default False)

    Returns:
        tuple: (dataframe, project_root_path)
    """
    results = []
    filtered_count = 0
    progress_bar = tqdm(desc="Parsing metadata", unit=" files")

    # Convert folder_path to Path object for easier manipulation
    base_path = Path(folder_path).resolve()

    # Initialize language analyzer components
    config = LanguageConfig()
    comment_detector = CommentDetector()
    file_walker = FileWalker(config)
    file_analyzer = FileAnalyzer(config, comment_detector, file_walker)

    try:
        for root, dirs, files in os.walk(folder_path):
            # Skip entire directories that are in our skip list
            dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]

            for file in files:
                file_path = os.path.join(root, file)

                # Check if file should be skipped
                skip, skip_reason = should_skip_file(file_path, file)

                if skip:
                    filtered_count += 1
                    if include_filtered:
                        # Convert absolute path to relative path
                        absolute_path = Path(file_path).resolve()
                        try:
                            relative_path = absolute_path.relative_to(base_path)
                        except ValueError:
                            relative_path = Path(file)

                        result = {
                            "filename": file,
                            "path": str(relative_path),
                            "file_type": "FILTERED",
                            "language": "Filtered",
                            "file_size": None,
                            "created_timestamp": None,
                            "last_modified": None,
                            "lines_of_code": None,
                            "skip_reason": skip_reason,
                            "status": "filtered",
                        }
                        results.append(result)
                    continue

                try:
                    file_type = get_file_type_safe(file_path)
                    file_size = os.path.getsize(file_path)
                    created_timestamp = os.path.getctime(file_path)
                    modified_timestamp = os.path.getmtime(file_path)

                    # Use the existing method from FileAnalyzer
                    language = file_analyzer.detect_language_by_extension(file_path)

                    # Calculate lines of code using FileAnalyzer's count_lines_of_code method
                    try:
                        file_stats = file_analyzer.count_lines_of_code(file_path, language)
                        lines_of_code = file_stats.code_lines if file_stats else None
                    except Exception as loc_error:
                        logger.warning("Could not calculate LOC for %s: %s", file_path, loc_error)
                        lines_of_code = None

                    # Convert absolute path to relative path from extracted directory
                    absolute_path = Path(file_path).resolve()
                    try:
                        relative_path = absolute_path.relative_to(base_path)
                    except ValueError:
                        relative_path = Path(file)

                    result = {
                        "filename": file,
                        "path": str(relative_path),
                        "file_type": file_type,
                        "language": language,
                        "file_size": file_size,
                        "created_timestamp": created_timestamp,
                        "last_modified": modified_timestamp,
                        "lines_of_code": lines_of_code,
                        "status": "success",
                    }
                    results.append(result)
                except Exception as exception:
                    # Convert absolute path to relative path for errors too
                    absolute_path = Path(file_path).resolve()
                    try:
                        relative_path = absolute_path.relative_to(base_path)
                    except ValueError:
                        relative_path = Path(file)

                    result = {
                        "filename": file,
                        "path": str(relative_path),
                        "file_type": "ERROR",
                        "language": "Unknown",
                        "file_size": None,
                        "created_timestamp": None,
                        "last_modified": None,
                        "lines_of_code": None,
                        "error": str(exception),
                        "status": "error",
                    }
                    results.append(result)

                # Progress bar update
                progress_bar.set_postfix(
                    {"folder": os.path.basename(root), "filtered": filtered_count}
                )
                progress_bar.update()
    finally:
        progress_bar.close()

    logger.info("Filtered out %d files", filtered_count)

    dataframe = pd.DataFrame(results)
    project_root = str(base_path)
    return dataframe, project_root


def save_metadata_json(
    dataframe: pd.DataFrame,
    output_filename: str = "metadata.json",
    project_root: str = None,
) -> str:
    """
    Converts metadata dataframe to clean JSON format and saves to outputs directory.

    Args:
        dataframe: DataFrame containing metadata from parse_metadata()
        output_filename: Name of output JSON file (default: "metadata.json")
        project_root: Absolute path to the project root directory

    Returns:
        str: Path to the saved JSON file
    """
    # Create outputs directory at project root level
    outputs_dir = Path.cwd() / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Clean and format the data
    cleaned_data = []

    for _, row in dataframe.iterrows():
        # Handle pandas NaN values properly
        file_size = row.get("file_size")
        if file_size is not None and not pd.isna(file_size):
            file_size = int(file_size)
        else:
            file_size = None

        created_ts = row.get("created_timestamp")
        if created_ts is not None and not pd.isna(created_ts):
            created_ts = float(created_ts)
        else:
            created_ts = None

        last_mod = row.get("last_modified")
        if last_mod is not None and not pd.isna(last_mod):
            last_mod = float(last_mod)
        else:
            last_mod = None

        # Handle lines of code
        lines_of_code = row.get("lines_of_code")
        if lines_of_code is not None and not pd.isna(lines_of_code):
            lines_of_code = int(lines_of_code)
        else:
            lines_of_code = None

        # Handle language field
        language = row.get("language")
        if language is not None and not pd.isna(language):
            language = str(language)
        else:
            language = "Unknown"

        # Create clean record with all fields from parse_metadata
        record = {
            "filename": str(row["filename"]),
            "path": str(row["path"]),
            "file_type": str(row["file_type"]),
            "language": language,
            "file_size": file_size,
            "lines_of_code": lines_of_code,
            "created_timestamp": created_ts,
            "last_modified": last_mod,
            "status": str(row.get("status", "success")),
        }

        # Add error information if present
        if "error" in row and row["error"] is not None and not pd.isna(row["error"]):
            record["error"] = str(row["error"])

        # Add skip reason if present (for filtered files)
        if (
            "skip_reason" in row
            and row["skip_reason"] is not None
            and not pd.isna(row["skip_reason"])
        ):
            record["skip_reason"] = str(row["skip_reason"])

        cleaned_data.append(record)

    # Calculate statistics including LOC
    successful_files = [
        r
        for r in cleaned_data
        if r["status"] == "success" and r["file_size"] is not None
    ]
    filtered_files = [r for r in cleaned_data if r["status"] == "filtered"]
    error_files = [r for r in cleaned_data if r["status"] == "error"]

    total_size = sum(r["file_size"] for r in successful_files) if successful_files else 0
    avg_size = total_size / len(successful_files) if successful_files else 0

    # Calculate total LOC
    files_with_loc = [r for r in successful_files if r["lines_of_code"] is not None]
    total_loc = sum(r["lines_of_code"] for r in files_with_loc) if files_with_loc else 0
    avg_loc = total_loc / len(files_with_loc) if files_with_loc else 0

    # Create final JSON structure with metadata
    json_output = {
        "metadata": {
            "generated_at": datetime.now().timestamp(),
            "total_files": len(cleaned_data),
            "successful_parses": len(successful_files),
            "failed_parses": len(error_files),
            "filtered_files": len(filtered_files),
            "total_size_bytes": total_size,
            "average_file_size_bytes": round(avg_size, 2),
            "total_lines_of_code": total_loc,
            "average_lines_of_code": round(avg_loc, 2),
            "files_with_loc": len(files_with_loc),
            "schema_version": "2.3",
        },
        "project_root": project_root,
        "files": cleaned_data,
    }

    # Save to outputs directory
    output_path = outputs_dir / output_filename

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)

        logger.info("Metadata saved to: %s", output_path)
        return str(output_path)

    except Exception as e:
        logger.error("Error saving metadata JSON: %s", e)
        raise
