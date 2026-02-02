from __future__ import annotations
from pathlib import Path
import zipfile
import os
import sys
import platform
import pytest

from src.core.validators.zip import validate_zip, validate_dir


def make_zip_with_entries(path: Path, entries: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)

def make_empty_zip(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED):
        pass


def test_validate_zip_ok(tmp_path: Path):
    z = tmp_path / "valid.zip"
    make_zip_with_entries(z, {"ok.txt": b"hello"})
    ok, errs = validate_zip(z)
    assert ok is True
    assert errs == []


def test_validate_zip_not_exist(tmp_path: Path):
    z = tmp_path / "missing.zip"
    ok, errs = validate_zip(z)
    assert ok is False
    assert "file does not exist" in errs


def test_validate_zip_bad_zip_file(tmp_path: Path):
    z = tmp_path / "bad.zip"
    z.write_bytes(b"this-is-not-a-real-zip")
    ok, errs = validate_zip(z)
    assert ok is False
    assert any("bad zip file" in e for e in errs)


def test_validate_zip_crc_error(tmp_path: Path):
    z = tmp_path / "broken_crc.zip"
    # If you already have a CRC corruption helper, import it instead.
    # For simplicity here, we create a small ZIP and corrupt the tail bytes manually.
    make_zip_with_entries(z, {"a.txt": b"aaa"})
    # Manually corrupt the tail (this may vary slightly by platform).
    with open(z, "r+b") as f:
        f.seek(-8, os.SEEK_END)
        b = f.read(1)
        f.seek(-8, os.SEEK_END)
        f.write(bytes([b[0] ^ 0xFF]))
    ok, errs = validate_zip(z)
    assert ok is False
    assert any(("crc error" in e) or ("bad zip file" in e) for e in errs)

# adding extra test cases below

def test_empty_zip_is_invalid_or_warn(tmp_path: Path):
    """An empty ZIP should be detected as an error or at least produce a warning."""
    z = tmp_path / "empty.zip"
    make_empty_zip(z)
    ok, errs = validate_zip(z)
    # Adjust "empty zip" message to match your implementation policy
    assert ok is False
    assert any("empty zip" in e.lower() for e in errs)


def test_zip_slip_parent_traversal_is_rejected(tmp_path: Path):
    """Paths containing '../' (Zip Slip) should be rejected."""
    z = tmp_path / "slip.zip"
    make_zip_with_entries(z, {"../evil.txt": b"bad"})
    ok, errs = validate_zip(z)
    assert ok is False
    assert any("zip slip" in e.lower() or "path traversal" in e.lower() for e in errs)


def test_absolute_path_entry_is_rejected(tmp_path: Path):
    """Absolute paths inside the archive should be rejected."""
    z = tmp_path / "abs.zip"
    names = ["/etc/passwd", "C:\\Windows\\system32\\drivers\\etc\\hosts"]
    make_zip_with_entries(z, {names[0]: b"x", names[1]: b"y"})
    ok, errs = validate_zip(z)
    assert ok is False
    assert any("absolute path" in e.lower() for e in errs)




def test_empty_file_detection(tmp_path: Path):
    """Empty files should at least be detected (policy may treat as ERROR or WARN)."""
    z = tmp_path / "empty_file.zip"
    make_zip_with_entries(z, {"empty.txt": b""})
    ok, errs = validate_zip(z)
    # TDD: Initially treat as ERROR; change here if policy later allows WARN.
    assert ok is False
    assert any("empty file" in e.lower() for e in errs)



def test_too_many_files_limit(tmp_path: Path):
    """Exceeding the file count limit should trigger an error."""
    z = tmp_path / "too_many.zip"
    entries = {f"f{i}.txt": b"x" for i in range(0, 5001)}  # Example limit: 5000
    make_zip_with_entries(z, entries)
    ok, errs = validate_zip(z)
    assert ok is False
    assert any("file count" in e.lower() or "too many files" in e.lower() for e in errs)


def test_deep_nesting_limit(tmp_path: Path):
    """Exceeding the directory depth limit should trigger an error."""
    z = tmp_path / "too_deep.zip"
    deep_name = "/".join(["lvl"] * 64) + "/leaf.txt"  # Example limit: 32
    make_zip_with_entries(z, {deep_name: b"x"})
    ok, errs = validate_zip(z)
    assert ok is False
    assert any("depth" in e.lower() or "too deep" in e.lower() for e in errs)


@pytest.mark.skipif(platform.system().lower() == "linux", reason="Case collision mainly relevant on case-insensitive FS")
def test_case_insensitive_name_collision(tmp_path: Path):
    """On case-insensitive file systems, names like A.txt and a.txt should be treated as duplicates."""
    z = tmp_path / "case_collision.zip"
    make_zip_with_entries(z, {"A.txt": b"x", "a.txt": b"y"})
    ok, errs = validate_zip(z)
    assert ok is False
    assert any("name collision" in e.lower() or "duplicate name" in e.lower() for e in errs)


def test_validate_dir_mixes_valid_and_invalid(tmp_path: Path):
    """Verify that directory scanning correctly handles mixed valid and invalid archives."""
    good = tmp_path / "good.zip"
    bad = tmp_path / "bad.zip"
    other = tmp_path / "note.txt"
    make_zip_with_entries(good, {"ok.txt": b"hello"})
    make_zip_with_entries(bad, {"../evil.txt": b"no"})  # Expected to fail Zip Slip check
    other.write_text("not a zip")

    results = validate_dir(tmp_path)
    # results: list[tuple[Path, bool, list[str]]]
    d = {p.name: (ok, errs) for p, ok, errs in results}

    assert d["good.zip"][0] is True and d["good.zip"][1] == []
    assert d["bad.zip"][0] is False and any("zip slip" in e.lower() or "path traversal" in e.lower() for e in d["bad.zip"][1])
    # note.txt behavior depends on validate_dir policy:
    # if “only validate .zip files”, it won’t appear in results.
    # if “validate all files”, it should appear as invalid.
