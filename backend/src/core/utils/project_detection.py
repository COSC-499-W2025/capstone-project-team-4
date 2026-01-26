"""
Utilities for detecting multiple projects inside a directory
(e.g. monorepos or multi-project ZIP uploads).
"""

from pathlib import Path
from typing import List

# Files that strongly indicate a project root
PROJECT_MARKERS = {
    "package.json",        # Node / frontend
    "pyproject.toml",      # Python modern
    "requirements.txt",    # Python legacy
    "setup.py",            # Python legacy
    "pom.xml",             # Java / Maven
    "build.gradle",        # Java / Gradle
    "Makefile",
    "Cargo.toml",          # Rust
    "go.mod",              # Go
}


def is_project_root(path: Path) -> bool:
    """Return True if directory looks like a project root."""
    if not path.is_dir():
        return False

    for marker in PROJECT_MARKERS:
        if (path / marker).exists():
            return True

    # fallback: directory with lots of source files
    source_files = list(path.rglob("*.py")) + list(path.rglob("*.js"))
    return len(source_files) >= 3


def detect_project_roots(root: Path) -> List[Path]:
    """
    Detect multiple project roots inside a directory.

    Rules:
    - If the root itself looks like a project → return [root]
    - Else, scan first-level subdirectories for project roots
    - Avoid deeply nested false positives
    """

    if is_project_root(root):
        return [root]

    projects: List[Path] = []

    for child in root.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            if is_project_root(child):
                projects.append(child)

    # Fallback: treat entire directory as single project
    return projects or [root]
