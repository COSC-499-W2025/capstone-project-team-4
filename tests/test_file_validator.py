# tests/test_file_validator.py
from __future__ import annotations
from pathlib import Path
import zipfile
import os

from src.core.file_validator import validate_zip, validate_dir

def make_valid_zip(path: Path, *, name: str = "ok.txt", content: str = "hello") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name, content)

def make_crc_broken_zip(path: Path) -> None:
    # CRC: It’s a type of checksum — a short number that helps detect accidental changes in data (like corruption or bit flips).
    make_valid_zip(path)
    with open(path, "r+b") as f:
        try:
            f.seek(-16, os.SEEK_END)
        except OSError:
            f.seek(0, os.SEEK_SET)
        chunk = bytearray(f.read(16))
        if not chunk:
            # If file is too small, corrupt at least one byte
            f.seek(0, os.SEEK_SET)
            b = f.read(1)
            if b:
                f.seek(0, os.SEEK_SET)
                f.write(bytes([b[0] ^ 0xFF]))
            return
        # Flip bits to corrupt
        for i in range(len(chunk)):
            chunk[i] ^= 0xAA
        f.seek(-len(chunk), os.SEEK_END)
        f.write(chunk)

def test_validate_zip_ok(tmp_path: Path):
    z = tmp_path / "valid.zip"
    make_valid_zip(z)
    ok, errs = validate_zip(z)
    assert ok is True
    assert errs == []


def test_validate_zip_not_exist(tmp_path: Path):
    z = tmp_path / "missing.zip"
    ok, errs = validate_zip(z)
    assert ok is False
    assert "file does not exist" in errs

def test_validate_zip_bad_zip_file(tmp_path: Path):
    # the inside is not ZIP
    z = tmp_path / "bad.zip"
    z.write_bytes(b"this-is-not-a-real-zip")
    ok, errs = validate_zip(z)
    assert ok is False
    assert any("bad zip file" in e for e in errs)

def test_validate_zip_crc_error(tmp_path: Path):
    # testing inside of ZIP
    z = tmp_path / "broken_crc.zip"
    make_crc_broken_zip(z)
    ok, errs = validate_zip(z)
    assert ok is False
    assert any(("crc error" in e) or ("bad zip file" in e) for e in errs)

