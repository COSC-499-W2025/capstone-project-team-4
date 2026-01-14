"""
Unified file walker for consistent directory traversal.

This module consolidates the directory walking logic that was previously
scattered across metadata_parser.py, language_analyzer.py, and
resume_skill_extractor.py.

Also provides FileInfo dataclass and collect_all_file_info() for
single-pass file metadata collection used by the analysis pipeline.
"""

import os
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Callable, Optional, Set, List, Union, Tuple

from src.core.constants import (
    SKIP_DIRECTORIES,
    SKIP_EXTENSIONS,
    SKIP_FILENAMES,
    HIDDEN_FILE_EXCEPTIONS,
    MAX_FILE_SIZE,
    MIN_FILE_SIZE,
    filter_directories,
)

logger = logging.getLogger(__name__)


# =============================================================================
# FileInfo dataclass for unified file metadata collection
# =============================================================================


@dataclass
class FileInfo:
    """
    Unified file information collected in a single pass.

    Used to share file metadata across multiple analysis steps
    (metadata parsing, skill extraction, complexity analysis)
    without redundant file system traversals.
    """
    path: Path
    relative_path: str
    filename: str
    extension: str
    size: int
    language: str
    lines_of_code: Optional[int]
    file_type: str
    created: float
    modified: float


class UnifiedFileWalker:
    """
    A unified file walker for consistent directory traversal across all core modules.

    This class consolidates the directory walking logic that was previously
    duplicated in metadata_parser.py, language_analyzer.py, and resume_skill_extractor.py.

    Attributes:
        skip_dirs: Set of directory names to skip
        skip_extensions: Set of file extensions to skip
        skip_filenames: Set of filenames to skip
        hidden_exceptions: Set of hidden files that should be analyzed
        max_file_size: Maximum file size to analyze
        min_file_size: Minimum file size to analyze
    """

    def __init__(
        self,
        skip_dirs: Optional[Set[str]] = None,
        skip_extensions: Optional[Set[str]] = None,
        skip_filenames: Optional[Set[str]] = None,
        hidden_exceptions: Optional[Set[str]] = None,
        max_file_size: int = MAX_FILE_SIZE,
        min_file_size: int = MIN_FILE_SIZE,
    ):
        """
        Initialize the file walker with optional custom filtering rules.

        Args:
            skip_dirs: Set of directory names to skip (default: SKIP_DIRECTORIES)
            skip_extensions: Set of file extensions to skip (default: SKIP_EXTENSIONS)
            skip_filenames: Set of filenames to skip (default: SKIP_FILENAMES)
            hidden_exceptions: Set of hidden files to analyze (default: HIDDEN_FILE_EXCEPTIONS)
            max_file_size: Maximum file size in bytes (default: MAX_FILE_SIZE)
            min_file_size: Minimum file size in bytes (default: MIN_FILE_SIZE)
        """
        self.skip_dirs = skip_dirs if skip_dirs is not None else SKIP_DIRECTORIES
        self.skip_extensions = skip_extensions if skip_extensions is not None else SKIP_EXTENSIONS
        self.skip_filenames = skip_filenames if skip_filenames is not None else SKIP_FILENAMES
        self.hidden_exceptions = hidden_exceptions if hidden_exceptions is not None else HIDDEN_FILE_EXCEPTIONS
        self.max_file_size = max_file_size
        self.min_file_size = min_file_size

    def walk(
        self,
        root_path: Union[str, Path],
        filter_fn: Optional[Callable[[Path], bool]] = None,
    ) -> Iterator[Path]:
        """
        Walk through a directory tree, yielding file paths that pass filtering.

        Args:
            root_path: The root directory to start walking from
            filter_fn: Optional additional filter function that takes a Path and returns bool

        Yields:
            Path objects for files that pass all filters
        """
        root = Path(root_path).resolve()

        for dirpath, dirnames, filenames in os.walk(root):
            # Filter out skip directories in-place to prevent descending into them
            dirnames[:] = [d for d in dirnames if d not in self.skip_dirs]

            for filename in filenames:
                file_path = Path(dirpath) / filename

                # Check if file should be analyzed
                if not self.should_analyze_file(file_path):
                    continue

                # Apply optional custom filter
                if filter_fn is not None and not filter_fn(file_path):
                    continue

                yield file_path

    def walk_with_info(
        self,
        root_path: Union[str, Path],
    ) -> Iterator[Tuple[Path, Optional[str]]]:
        """
        Walk through a directory tree, yielding file paths and skip reasons.

        Args:
            root_path: The root directory to start walking from

        Yields:
            Tuples of (Path, skip_reason) where skip_reason is None if file should be analyzed
        """
        root = Path(root_path).resolve()

        for dirpath, dirnames, filenames in os.walk(root):
            # Filter out skip directories in-place
            dirnames[:] = [d for d in dirnames if d not in self.skip_dirs]

            for filename in filenames:
                file_path = Path(dirpath) / filename
                skip, reason = self.should_skip_file(file_path)
                yield file_path, reason if skip else None

    def should_analyze_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be analyzed.

        Args:
            file_path: Path to the file

        Returns:
            True if the file should be analyzed, False otherwise
        """
        skip, _ = self.should_skip_file(file_path)
        return not skip

    def should_skip_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Determine if a file should be skipped and why.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (should_skip: bool, reason: str)
        """
        filename = file_path.name
        extension = file_path.suffix.lower()

        # Check hidden files (except allowed ones)
        if filename.startswith('.') and filename not in self.hidden_exceptions:
            return True, f"hidden file: {filename}"

        # Check file extension
        if extension in self.skip_extensions:
            return True, f"skipped extension: {extension}"

        # Check filename
        if filename in self.skip_filenames:
            return True, f"skipped filename: {filename}"

        # Check if file is in a skipped directory (for nested checks)
        for part in file_path.parts:
            if part in self.skip_dirs:
                return True, f"in skipped directory: {part}"

        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                return True, f"file too large: {file_size} bytes (max: {self.max_file_size})"
            if file_size < self.min_file_size:
                return True, f"file too small: {file_size} bytes (min: {self.min_file_size})"
        except OSError as e:
            logger.warning("Could not get file size for %s: %s", file_path, e)
            # Let it through if we can't get the size

        return False, ""

    def count_files(self, root_path: Union[str, Path]) -> int:
        """
        Count the number of files that would be analyzed.

        Args:
            root_path: The root directory to count files in

        Returns:
            Number of files that pass filtering
        """
        return sum(1 for _ in self.walk(root_path))

    def get_filtered_count(self, root_path: Union[str, Path]) -> Tuple[int, int]:
        """
        Count both analyzable and filtered files.

        Args:
            root_path: The root directory to count files in

        Returns:
            Tuple of (analyzable_count, filtered_count)
        """
        analyzable = 0
        filtered = 0

        for _, skip_reason in self.walk_with_info(root_path):
            if skip_reason is None:
                analyzable += 1
            else:
                filtered += 1

        return analyzable, filtered


# Convenience function for simple use cases
def walk_source_files(
    root_path: Union[str, Path],
    skip_dirs: Optional[Set[str]] = None,
) -> Iterator[Path]:
    """
    Convenience function to walk source files with default or custom skip dirs.

    Args:
        root_path: The root directory to walk
        skip_dirs: Optional custom set of directories to skip

    Yields:
        Path objects for source files
    """
    walker = UnifiedFileWalker(skip_dirs=skip_dirs)
    yield from walker.walk(root_path)


# =============================================================================
# Single-pass file info collection
# =============================================================================


def collect_all_file_info(
    root_path: Union[str, Path],
    show_progress: bool = True,
) -> List[FileInfo]:
    """
    Collect all file information in a single pass through the project.

    This function performs one traversal of the file system and collects
    all metadata needed by the analysis pipeline, including:
    - File paths and sizes
    - Language detection
    - Lines of code
    - File types (MIME)
    - Timestamps

    Args:
        root_path: The root directory to walk
        show_progress: Whether to show a progress bar (default True)

    Returns:
        List of FileInfo objects with all metadata
    """
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
    from tqdm import tqdm
    import mimetypes
    import magic

    from src.core.detectors.language import (
        LanguageConfig,
        FileAnalyzer,
        CommentDetector,
        FileWalker as LangFileWalker,
    )

    root = Path(root_path).resolve()
    results: List[FileInfo] = []

    # Initialize language analyzer components (reuse across all files)
    config = LanguageConfig()
    comment_detector = CommentDetector()
    lang_file_walker = LangFileWalker(config)
    file_analyzer = FileAnalyzer(config, comment_detector, lang_file_walker)

    # Helper for safe MIME detection with timeout
    def get_file_type_safe(file_path: str, timeout: float = 5.0) -> str:
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(magic.from_file, file_path, mime=True)
                return future.result(timeout=timeout)
        except (FuturesTimeoutError, Exception):
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or "application/octet-stream"

    walker = UnifiedFileWalker()
    file_paths = list(walker.walk(root))

    iterator = tqdm(file_paths, desc="Collecting file info", unit=" files") if show_progress else file_paths

    for file_path in iterator:
        try:
            stat = file_path.stat()

            # Relative path from root
            try:
                relative_path = str(file_path.relative_to(root))
            except ValueError:
                relative_path = file_path.name

            # Language detection
            language = file_analyzer.detect_language_by_extension(str(file_path))

            # Lines of code
            lines_of_code = None
            try:
                file_stats = file_analyzer.count_lines_of_code(str(file_path), language)
                lines_of_code = file_stats.code_lines if file_stats else None
            except Exception:
                pass

            # MIME type
            file_type = get_file_type_safe(str(file_path))

            info = FileInfo(
                path=file_path,
                relative_path=relative_path,
                filename=file_path.name,
                extension=file_path.suffix.lower(),
                size=stat.st_size,
                language=language,
                lines_of_code=lines_of_code,
                file_type=file_type,
                created=stat.st_ctime,
                modified=stat.st_mtime,
            )
            results.append(info)

        except Exception as e:
            logger.warning(f"Error collecting info for {file_path}: {e}")
            continue

    return results


def file_info_to_metadata_dict(file_info: FileInfo) -> dict:
    """
    Convert FileInfo to the dictionary format expected by parse_metadata.

    Args:
        file_info: FileInfo object

    Returns:
        Dictionary matching parse_metadata output format
    """
    return {
        "filename": file_info.filename,
        "path": file_info.relative_path,
        "file_type": file_info.file_type,
        "language": file_info.language,
        "file_size": file_info.size,
        "created_timestamp": file_info.created,
        "last_modified": file_info.modified,
        "lines_of_code": file_info.lines_of_code,
        "status": "success",
    }
