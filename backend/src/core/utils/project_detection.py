from __future__ import annotations
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

    if is_monorepo_root(root):
        return [root]

    projects: List[Path] = []

    def depth(p: Path) -> int:
        try:
            return len(p.resolve().relative_to(root).parts)
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
    projects = sorted(projects, key=lambda x: (len(x.resolve().relative_to(root).parts), x.name.lower()))


    # Remove roots that are inside another detected root
    filtered: List[Path] = []
    for p in projects:
        p_resolved = p.resolve()
        if not any(p_resolved.is_relative_to(parent.resolve()) for parent in filtered):  # py3.9+ has is_relative_to
            filtered.append(p)

    if len(filtered) >= 2:
    # If this looks like a monorepo, analyze at the root level
        if is_monorepo_root(root):
            return [root]
        return filtered


    if len(filtered) == 1:
        return filtered
    
    return [root]



def _has_monorepo_marker(root: Path) -> bool:
    """
    Marker files that strongly suggest this folder is a real repo root / monorepo root.
    Use files (not directories) to avoid false positives.
    """
    markers = (
        ".gitignore",
        "README.md",
        "readme.md",
        "docker-compose.yml",
        "pnpm-workspace.yaml",
        "lerna.json",
        "turbo.json",
        "nx.json",
    )
    return any((root / m).is_file() for m in markers)


def is_monorepo_root(root: Path, max_depth: int = 2) -> bool:

    if not root.is_dir():
        return False

    if not _has_monorepo_marker(root):
        return False

    def depth(p: Path) -> int:
        try:
            return len(p.resolve().relative_to(root).parts)
        except ValueError:
            return 999

    found = 0
    for p in root.rglob("*"):
        if not p.is_dir():
            continue
        if _is_ignored_dir(p):
            continue
        if depth(p) > max_depth:
            continue

        if is_project_root(p):
            found += 1
            if found >= 2:
                return True

    return False