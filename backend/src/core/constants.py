"""
Unified constants for the core analysis modules.

This module consolidates all skip directories, extensions, filenames, and size limits
that were previously scattered across metadata_parser.py, language_analyzer.py,
resume_skill_extractor.py, and project_analyzer.py.
"""

from typing import FrozenSet

# =============================================================================
# SKIP DIRECTORIES - Directories to exclude from analysis
# =============================================================================

SKIP_DIRECTORIES: FrozenSet[str] = frozenset(
    {
        # Version control
        ".git",
        ".svn",
        ".hg",
        ".bzr",
        # Python
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".coverage",
        "htmlcov",
        ".tox",
        ".nox",
        "venv",
        ".venv",
        "env",
        ".env",
        "virtualenv",
        "build",
        "dist",
        ".eggs",
        # Node.js / JavaScript
        "node_modules",
        ".npm",
        ".yarn",
        # Java / JVM
        "target",
        ".gradle",
        ".m2",
        # IDE and editors
        ".vscode",
        ".idea",
        ".vs",
        ".vscode-test",
        # Logs and temporary files
        "logs",
        "tmp",
        "temp",
        ".tmp",
        ".temp",
        # Dependencies and libraries
        "vendor",
        "bower_components",
        "jspm_packages",
        # Documentation build
        "_build",
        "site",
        # Testing / Coverage
        "coverage",
        ".nyc_output",
    }
)


# =============================================================================
# SKIP EXTENSIONS - File extensions to exclude from analysis
# =============================================================================

SKIP_EXTENSIONS: FrozenSet[str] = frozenset(
    {
        # Compiled files
        ".pyc",
        ".pyo",
        ".class",
        ".o",
        ".obj",
        ".so",
        ".dylib",
        ".dll",
        ".exe",
        # Logs / temp
        ".log",
        ".tmp",
        ".temp",
        ".swp",
        ".swo",
        ".bak",
        ".backup",
        # OS / cache
        ".DS_Store",
        ".cache",
        # Documents
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        # Images
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".bmp",
        ".ico",
        ".svg",
        # Archives
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        # Media
        ".mp3",
        ".mp4",
        ".mov",
        ".wav",
    }
)


# =============================================================================
# SKIP FILENAMES - Specific filenames to exclude from analysis
# =============================================================================

SKIP_FILENAMES: FrozenSet[str] = frozenset(
    {
        # System files
        ".DS_Store",
        "Thumbs.db",
        "ehthumbs.db",
        "Desktop.ini",
        # Log files
        "npm-debug.log",
        "yarn-debug.log",
        "yarn-error.log",
        # Lock files (often large and not source code)
        "package-lock.json",
        "yarn.lock",
        "Pipfile.lock",
        "poetry.lock",
        "composer.lock",
        "Gemfile.lock",
        # IDE files (when appearing as files, not directories)
        ".vscode",
        ".idea",
    }
)


# =============================================================================
# HIDDEN FILE EXCEPTIONS - Hidden files that SHOULD be analyzed
# =============================================================================

HIDDEN_FILE_EXCEPTIONS: FrozenSet[str] = frozenset(
    {
        ".gitignore",
        ".env",
        ".dockerignore",
        ".editorconfig",
        ".prettierrc",
        ".eslintrc",
        ".babelrc",
    }
)


# =============================================================================
# SIZE LIMITS
# =============================================================================

MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB - maximum file size to analyze
MIN_FILE_SIZE: int = 1  # 1 byte - minimum file size to analyze

# Alternative smaller limit for certain operations (e.g., line counting)
DEFAULT_MAX_SIZE: int = 1_000_000  # 1MB


# =============================================================================
# FILE VALIDATION LIMITS (from zip_file_validator.py)
# =============================================================================

MAX_FILES_IN_ARCHIVE: int = 100  # Maximum number of files in a ZIP archive
MAX_NESTING_DEPTH: int = 10  # Maximum directory nesting depth


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def should_skip_directory(dirname: str) -> bool:
    """
    Check if a directory should be skipped during traversal.

    Args:
        dirname: The name of the directory (not the full path)

    Returns:
        True if the directory should be skipped, False otherwise
    """
    return dirname in SKIP_DIRECTORIES


def should_skip_file_by_extension(extension: str) -> bool:
    """
    Check if a file should be skipped based on its extension.

    Args:
        extension: The file extension (including the dot, e.g., '.pyc')

    Returns:
        True if the file should be skipped, False otherwise
    """
    return extension.lower() in SKIP_EXTENSIONS


def should_skip_file_by_name(filename: str) -> bool:
    """
    Check if a file should be skipped based on its name.

    Args:
        filename: The name of the file (not the full path)

    Returns:
        True if the file should be skipped, False otherwise
    """
    return filename in SKIP_FILENAMES


def is_hidden_file_exception(filename: str) -> bool:
    """
    Check if a hidden file is an exception that should be analyzed.

    Args:
        filename: The name of the file (not the full path)

    Returns:
        True if this hidden file should be analyzed, False otherwise
    """
    return filename in HIDDEN_FILE_EXCEPTIONS


def filter_directories(directories: list[str]) -> list[str]:
    """
    Filter a list of directories, removing those that should be skipped.

    Args:
        directories: List of directory names

    Returns:
        Filtered list with skip directories removed
    """
    return [d for d in directories if d not in SKIP_DIRECTORIES]
