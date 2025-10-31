from __future__ import annotations
import argparse
from pathlib import Path
from pprint import pprint

# from src.core.file_validator import validate_zip
from .file_validator import validate_zip, validate_dir
from .run import validate_and_parse


def main():
    ap = argparse.ArgumentParser(description="ZIP validator + metadata parser")
    ap.add_argument(
        "path",
        nargs="?",
        default="tests/zips",
        help="Path to a ZIP file or directory (defaults to tests/zips if not specified).",
    )
    ap.add_argument(
        "--parse",
        action="store_true",
        help="If a ZIP file is valid, also parse the metadata of its contents (using a temporary directory).",
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
            if ok and args.parse:
                pack = validate_and_parse(p)
                if pack["metadata"] is not None:
                    print(f"— Parsed metadata rows: {len(pack['metadata'])}")
    else:
        if args.parse:
            pack = validate_and_parse(target)
            mark = "✅" if pack["is_valid"] else "❌"
            print(f"{mark} {pack['zip_name']}")
            if pack["validation_errors"]:
                pprint(pack["validation_errors"])
            if pack["metadata"] is not None:
                print(pack["metadata"].head())
        else:
            ok, errs = validate_zip(target)
            if ok:
                print(f"✅ {target} is valid.")
            else:
                print(f"❌ {target} is invalid.")
                for e in errs:
                    print("  -", e)


if __name__ == "__main__":
    main()
