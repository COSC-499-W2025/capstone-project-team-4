from __future__ import annotations
from pathlib import Path
import zipfile
import tempfile
from typing import Optional, Dict, Any

from .file_validator import validate_zip, validate_dir
from .metadata_parser import parse_metadata


def validate_and_parse(zip_path: str | Path) -> Dict[str, Any]:
    # Validate a ZIP file, and if valid, extract it to a temporary directory and parse its metadata."""
    zip_path = Path(zip_path)
    ok, errs = validate_zip(zip_path)
    if not ok:
        return {
            "zip_name": zip_path.name,
            "is_valid": False,
            "validation_errors": errs,
            "metadata": None,
        }

    with tempfile.TemporaryDirectory(prefix="zip_extract_") as tmpdir:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)
        df = parse_metadata(tmpdir)  # Analyze the extracted temporary directory
        # The temporary directory is automatically cleaned up when the context exits
        return {
            "zip_name": zip_path.name,
            "is_valid": True,
            "validation_errors": [],
            "metadata": df,
        }
