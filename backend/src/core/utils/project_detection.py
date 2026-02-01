from __future__ import annotations
from logging import root
from pathlib import Path
from typing import List

PROJECT_MARKERS = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "pom.xml",
    "build.gradle",
    "Makefile",
    "Cargo.toml",
    "go.mod",
}

IGNORE_DIRS = {
    "__MACOSX",
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".idea",
    ".vscode",
}

CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp", ".cs"}


def _is_ignored_dir(p: Path) -> bool:
    return p.name in IGNORE_DIRS or p.name.startswith(".")


def is_project_root(path: Path, min_code_files: int = 3, max_scan_files: int = 400) -> bool:
    """Heuristic project root detector that avoids scanning into .venv/node_modules/etc."""
    if not path.is_dir() or _is_ignored_dir(path):
        return False

    # Strong markers
    for marker in PROJECT_MARKERS:
        if (path / marker).exists():
            return True

    # Lightweight code-file count (bounded, prunes ignored dirs)
    count = 0
    scanned = 0
    for p in path.rglob("*"):
        if scanned >= max_scan_files:
            break
        scanned += 1

        if p.is_dir() and _is_ignored_dir(p):
            # rglob can't truly prune, but we can skip quickly
            continue

        if p.is_file() and p.suffix.lower() in CODE_EXTS:
            # ignore code inside ignored dirs
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            count += 1
            if count >= min_code_files:
                return True

    return False


def detect_project_roots(root: Path, max_depth: int = 4) -> List[Path]:
    """
    Detect multiple project roots (recursive + depth-limited), while ignoring junk/env folders.
    Once a root is detected, we do not descend further into it.
    """
    root = root.resolve()

    projects: List[Path] = []

    def depth(p: Path) -> int:
        try:
            return len(p.relative_to(root).parts)
        except ValueError:
            return 999

    # walk tree, but stop deep + avoid ignored dirs
    for p in root.rglob("*"):
        if not p.is_dir():
            continue
        if _is_ignored_dir(p):
            continue
        if depth(p) > max_depth:
            continue

        if is_project_root(p):
            projects.append(p)

    # If we found nested projects, prefer the shallowest ones
    projects = sorted(projects, key=lambda x: (len(x.relative_to(root).parts), x.name.lower()))


    # Remove roots that are inside another detected root
    filtered: List[Path] = []
    for p in projects:
        if not any(p.is_relative_to(parent) for parent in filtered):  # py3.9+ has is_relative_to
            filtered.append(p)

    if len(filtered) >= 2:
        return filtered


    if len(filtered) == 1:
        return filtered
    
    return [root]

