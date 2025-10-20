# parse_zip_structure.py
# ---------------------------------
# Prompt the user for a ZIP file path, safely extracts it to a
# temporary directory, recursively parses all nested folders and files,
# and prints a directory-like structure.

# Example Output:
# ├── project/
# │   ├── src/
# │   │   └── main.py
# │   ├── README.md
# │   └── requirements.txt


import tempfile
from pathlib import Path
from zipfile import ZipFile, BadZipFile

def extract_zip_safe(zip_path: Path, dest: Path) -> Path:
    # Extracts a ZIP archive safely into 'dest' directory.
    # Protects against ZipSlip (malicious paths like ../../etc/passwd).
    
    try:
        with ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                # Resolve full path of extracted file
                target_path = (dest / member.filename).resolve()
                # Check that it's within 'dest'
                if not str(target_path).startswith(str(dest.resolve())):
                    raise ValueError(f"Unsafe path detected in ZIP: {member.filename}")
            zf.extractall(dest)
        return dest
    except BadZipFile:
        raise ValueError("Invalid or corrupted ZIP file.")


def build_directory_tree(root: Path, prefix: str = "") -> str:
    # Recursively builds a tree-like string representation of the directory structure.
    
    entries = sorted(list(root.iterdir()))
    tree_lines = []
    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        line = f"{prefix}{connector}{entry.name}"
        tree_lines.append(line)
        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            tree_lines.append(build_directory_tree(entry, prefix + extension))
    return "\n".join(tree_lines)

def main():
    # 1. Ask user for ZIP path
    raw_path = input("Enter path to your ZIP file: ").strip()
    zip_path = Path(raw_path).expanduser().resolve()

    # 2. Validate path
    if not zip_path.exists():
        print(f"File not found: {zip_path}")
        return
    if zip_path.suffix.lower() != ".zip":
        print("The file must be a .zip archive.")
        return

    # 3. Extract safely to a temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        try:
            extract_zip_safe(zip_path, tmp_path)
        except ValueError as e:
            print(f"Error: {e}")
            return

        # 4. Find the top-level folder (if any)
        entries = list(tmp_path.iterdir())
        if len(entries) == 1 and entries[0].is_dir():
            root = entries[0]
        else:
            root = tmp_path

        # 5. Build and print directory structure
        print(f"\n Directory structure of {zip_path.name}:\n")
        tree_output = build_directory_tree(root)
        print(tree_output)


if __name__ == "__main__":
    main()
