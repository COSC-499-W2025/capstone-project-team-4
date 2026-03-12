"""
ZIP file validation module.

Provides validation for ZIP files to ensure they are safe and properly formatted.

Migrated from src/core/zip_file_validator.py
Updated to use constants from src/core/constants.py
"""

import logging
import zipfile
from pathlib import Path, PurePosixPath
from typing import List, Tuple

from src.core.constants import MAX_FILES_IN_ARCHIVE, MAX_NESTING_DEPTH

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".zip"}


def validate_zip(file_path: str | Path) -> Tuple[bool, List[str]]:
    """
    Validate a ZIP file for security and integrity.

    Checks:
    - File exists and is a valid file
    - Has .zip extension
    - Is a valid ZIP archive
    - Not empty
    - No absolute paths
    - No path traversal (zip slip vulnerability)
    - No empty files
    - Nesting depth within limits
    - No case-insensitive name collisions
    - File count within limits
    - CRC integrity

    Args:
        file_path: Path to the ZIP file

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    p = Path(file_path)

    # Existence check first
    if not p.exists():
        return (False, ["file does not exist"])

    # Must be a file (not a directory)
    if not p.is_file():
        return (False, ["not a file"])

    # File extension check
    if p.suffix.lower() not in ALLOWED_EXTENSIONS:
        return (False, [f"invalid extension: {p.suffix}"])

    # Quick MIME/structure check: not a ZIP at all
    if not zipfile.is_zipfile(p):
        return (False, ["bad zip file (cannot open)"])

    # ZIP structure and content checks
    try:
        with zipfile.ZipFile(p, "r") as zf:
            infos = zf.infolist()

            # Empty archive
            if len(infos) == 0:
                return (False, ["empty zip file"])

            # Collect state for cross-entry checks
            seen_lower: dict[str, str] = {}
            file_count = 0

            for zi in infos:
                name = zi.filename

                # Skip directory entries for some checks but count dirs differently
                is_dir = zi.is_dir() if hasattr(zi, "is_dir") else name.endswith("/")

                pp = PurePosixPath(name)

                # Absolute path entry
                if pp.is_absolute() or (len(name) > 0 and name.startswith("/")):
                    return (False, [f"absolute path entry: {name}"])

                # Parent traversal (zip slip)
                if ".." in pp.parts:
                    return (False, [f"path traversal entry: {name}"])

                # Count files (not directories)
                if not is_dir:
                    file_count += 1
                    # Empty file inside
                    if zi.file_size == 0:
                        return (False, [f"empty file in archive: {name}"])

                # Nesting depth (ignore leading/trailing empty parts)
                depth = len([p for p in pp.parts if p not in ("", ".")])
                if depth > MAX_NESTING_DEPTH:
                    return (False, [f"too deep nesting: {name}"])

                # Case-insensitive collision detection
                # Normalize by stripping any trailing slash for directories
                norm = str(pp).rstrip("/").lower()
                if norm in seen_lower:
                    return (
                        False,
                        [
                            f"case-insensitive name collision: {name} vs {seen_lower[norm]}"
                        ],
                    )
                seen_lower[norm] = name

            # File count limit
            if file_count > MAX_FILES_IN_ARCHIVE:
                return (
                    False,
                    [f"too many files: {file_count} (limit {MAX_FILES_IN_ARCHIVE})"],
                )

            # CRC / internal zip integrity
            bad_member = zf.testzip()
            if bad_member is not None:
                return (False, [f"crc error in entry: {bad_member}"])

    except zipfile.BadZipFile:
        return (False, ["bad zip file (cannot open)"])
    except Exception as e:
        logger.warning("Unexpected error validating ZIP: %s", e)
        return (False, [f"unexpected error: {e!r}"])

    return (True, [])


def validate_dir(dir_path: str | Path) -> List[Tuple[Path, bool, List[str]]]:
    """
    Validate all ZIP files in a directory.

    Args:
        dir_path: Path to the directory

    Returns:
        List of (path, is_valid, errors) tuples for each file
    """
    d = Path(dir_path)
    results: List[Tuple[Path, bool, List[str]]] = []

    if not d.exists():
        return [(d, False, ["directory does not exist"])]

    for p in sorted(d.iterdir()):
        if p.is_file():
            ok, errs = validate_zip(p)
            results.append((p, ok, errs))

    return results
