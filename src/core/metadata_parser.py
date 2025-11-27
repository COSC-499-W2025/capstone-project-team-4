import os
import json
import magic
from datetime import datetime
from pathlib import Path

import pandas as po
from tqdm import tqdm

from .language_analyzer import LanguageConfig, FileAnalyzer, CommentDetector, FileWalker


SKIP_DIRECTORIES = {
    '.git', '.svn', '.hg', '.bzr',
    '__pycache__', '.pytest_cache', '.mypy_cache', '.coverage', 'htmlcov',
    '.tox', '.nox', 'venv', '.venv', 'env', '.env', 'virtualenv',
    'build', 'dist', '*.egg-info', '.eggs',
    'node_modules', '.npm', '.yarn',
    'target', '.gradle', '.m2',
    '.vscode', '.idea',
    'logs', 'tmp', 'temp',
    'vendor', 'bower_components',
}
SKIP_EXTENSIONS = {'.pyc', '.log', '.tmp', '.bak', '.cache'}
SKIP_FILENAMES = {'.DS_Store', 'npm-debug.log', 'package-lock.json'}

MAX_FILE_SIZE = 50 * 1024 * 1024
MIN_FILE_SIZE = 1


def should_skip_file(file_path: str, file_name: str):
    path_obj = Path(file_path)

    if path_obj.suffix.lower() in SKIP_EXTENSIONS:
        return True, f"skipped extension: {path_obj.suffix}"

    if file_name in SKIP_FILENAMES:
        return True, f"skipped filename: {file_name}"

    if any(part in SKIP_DIRECTORIES for part in path_obj.parts):
        return True, "skipped directory match"

    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            return True, f"file too large: {file_size}"
        if file_size < MIN_FILE_SIZE:
            return True, f"file too small"
    except Exception:
        pass

    return False, ""


def parse_metadata(folder_path: str, include_filtered: bool = False):
    results = []
    filtered = 0
    progress = tqdm(desc="Parsing metadata", unit=" files")
    base = Path(folder_path).resolve()

    config = LanguageConfig()
    file_walker = FileWalker(config)
    comment_detector = CommentDetector()
    analyzer = FileAnalyzer(config, comment_detector, file_walker)

    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]

        for file in files:
            file_path = os.path.join(root, file)
            skip, reason = should_skip_file(file_path, file)

            if skip:
                filtered += 1
                if include_filtered:
                    absolute = Path(file_path).resolve()
                    try:
                        relative = absolute.relative_to(base)
                    except ValueError:
                        relative = Path(file)
                    results.append({
                        "filename": file, "path": str(relative), "file_type": "FILTERED",
                        "language": "Filtered", "file_size": None,
                        "created_timestamp": None, "last_modified": None,
                        "lines_of_code": None, "skip_reason": reason, "status": "filtered"
                    })
                continue

            try:
                file_type = magic.from_file(file_path, mime=True)
                size = os.path.getsize(file_path)
                created = os.path.getctime(file_path)
                modified = os.path.getmtime(file_path)
                language = analyzer.detect_language_by_extension(file_path)

                try:
                    loc_stats = analyzer.count_lines_of_code(file_path, language)
                    lines = loc_stats.code_lines if loc_stats else None
                except Exception:
                    lines = None

                absolute = Path(file_path).resolve()
                try:
                    relative = absolute.relative_to(base)
                except ValueError:
                    relative = Path(file)

                results.append({
                    "filename": file, "path": str(relative),
                    "file_type": file_type, "language": language,
                    "file_size": size, "lines_of_code": lines,
                    "created_timestamp": created, "last_modified": modified,
                    "status": "success"
                })
            except Exception as e:
                absolute = Path(file_path).resolve()
                try:
                    relative = absolute.relative_to(base)
                except ValueError:
                    relative = Path(file)

                results.append({
                    "filename": file, "path": str(relative), "file_type": "ERROR",
                    "language": "Unknown", "file_size": None,
                    "lines_of_code": None,
                    "created_timestamp": None, "last_modified": None,
                    "error": str(e), "status": "error"
                })

            progress.update()

    progress.close()
    dataframe = po.DataFrame(results)
    return dataframe, str(base)


def save_metadata_json(dataframe: po.DataFrame, output_filename: str | None, project_root: str):
    cleaned = []
    for _, row in dataframe.iterrows():
        cleaned.append({
            "filename": str(row["filename"]),
            "path": str(row["path"]),
            "file_type": str(row["file_type"]),
            "language": str(row.get("language", "Unknown")),
            "file_size": int(row["file_size"]) if row.get("file_size") else None,
            "lines_of_code": int(row["lines_of_code"]) if row.get("lines_of_code") else None,
            "created_timestamp": float(row["created_timestamp"]) if row.get("created_timestamp") else None,
            "last_modified": float(row["last_modified"]) if row.get("last_modified") else None,
            "status": str(row.get("status", "success"))
        })

    success = [f for f in cleaned if f["status"] == "success"]
    error = [f for f in cleaned if f["status"] == "error"]
    filtered = [f for f in cleaned if f["status"] == "filtered"]

    total_size = sum(f["file_size"] for f in success if f["file_size"]) if success else 0
    avg_size = total_size / len(success) if success else 0
    loc_files = [f for f in success if f["lines_of_code"] not in (None, 0)]
    total_loc = sum(f["lines_of_code"] for f in loc_files) if loc_files else 0
    avg_loc = total_loc / len(loc_files) if loc_files else 0

    json_output = {
        "metadata": {
            "generated_at": datetime.now().timestamp(),
            "total_files": len(cleaned),
            "successful_parses": len(success),
            "failed_parses": len(error),
            "filtered_files": len(filtered),
            "total_size_bytes": total_size,
            "average_file_size_bytes": round(avg_size, 2),
            "total_lines_of_code": total_loc,
            "average_lines_of_code": round(avg_loc, 2),
            "files_with_loc": len(loc_files),
            "schema_version": "2.3"
        },
        "project_root": project_root,
        "files": cleaned
    }

    # ⚠ Write to disk ONLY if output_filename is provided
    if output_filename:
        outputs_dir = Path.cwd() / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        output_path = outputs_dir / output_filename
        output_path.write_text(json.dumps(json_output, indent=2))
        return str(output_path)

    # 👍 If no filename → return JSON dict without writing to disk
    return json_output
