from pathlib import Path
import zipfile
from typing import List, Tuple
import argparse
from pprint import pprint

ALLOWED_EXTENSIONS = {".zip"}

def validate_zip(file_path: str | Path) -> Tuple[bool, List[str]]:

    errors: List[str] = []
    p = Path(file_path)

    # File extension check
    if p.suffix.lower() not in ALLOWED_EXTENSIONS:
        errors.append(f"invalid extension: {p.suffix}")

    # Existence check
    if not p.exists():
        errors.append("file does not exist")
        return (False, errors)

    # ZIP structure check
    try:
        with zipfile.ZipFile(p, "r") as zf:
            bad_member = zf.testzip()  # If none CRC OK,CRC is a checksum that detects data corruption in ZIP file entries.
            if bad_member is not None:
                errors.append(f"crc error in entry: {bad_member}")
    except zipfile.BadZipFile:
        errors.append("bad zip file (cannot open)")
    except Exception as e:
        errors.append(f"unexpected error: {e!r}")

    return (len(errors) == 0, errors)

def validate_dir(dir_path: str | Path) -> list[tuple[Path, bool, list[str]]]:
    d = Path(dir_path)
    results: list[tuple[Path, bool, list[str]]] = []
    if not d.exists():
        return [(d, False, ["directory does not exist"])]

    for p in sorted(d.iterdir()):
        if p.is_file():
            ok, errs = validate_zip(p)
            results.append((p, ok, errs))
    return results

if __name__ == "__main__":
    # By default checking tests/zips
    ap = argparse.ArgumentParser(description="Validate ZIP file(s)")
    ap.add_argument(
        "path",
        nargs="?",
        default="tests/zips",
        help="Relative or absolute path to a ZIP file or directory (defaults to tests/zips if not specified).",
    )


    args = ap.parse_args()

    target = Path(args.path)

    if target.is_dir():
        print(f"📂 Scanning directory: {target.resolve()}")
        results = validate_dir(target)
        for p, ok, errs in results:
            mark = "✅" if ok else "❌"
            print(f"{mark} {p.name}")
            if errs:
                pprint(errs)
    else:
        ok, errs = validate_zip(target)
        if ok:
            print(f"✅ {target} is valid.")
        else:
            print(f"❌ {target} is invalid.")
            for e in errs:
                print("  -", e)
