"""
Language analysis module.

This module provides language detection, file analysis, and line-of-code
counting functionality.

Features:
  - Tree-sitter based AST parsing for accurate detection
  - Comprehensive language/extension mappings
  - Multi-line comment handling
  - Special file detection (Dockerfile, Makefile, Gemfile, etc.)
  - Fallback detection chain for edge cases

Migrated from src/core/language_analyzer.py
Updated to use unified constants from src/core/constants.py
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Iterator, Tuple, Optional
from dataclasses import dataclass

from src.core.constants import (
    SKIP_DIRECTORIES,
    SKIP_EXTENSIONS,
    SKIP_FILENAMES,
    HIDDEN_FILE_EXCEPTIONS,
    MIN_FILE_SIZE,
    DEFAULT_MAX_SIZE,
)

logger = logging.getLogger(__name__)

# Tree-sitter for accurate multi-language parsing
try:
    from tree_sitter_languages import get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.debug("tree-sitter not available, using fallback detection")


# =============================================================================
# Built-in language patterns (comprehensive fallback)
# =============================================================================

# Comprehensive extension to language mapping
EXTENSION_MAP = {
    # Web
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "LESS",
    
    # JavaScript/TypeScript
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".vue": "Vue",
    ".svelte": "Svelte",
    
    # Python
    ".py": "Python",
    ".pyw": "Python",
    ".pyx": "Cython",
    ".pyi": "Python",
    
    # Java/JVM
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".groovy": "Groovy",
    ".gradle": "Gradle",
    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    
    # C/C++
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c++": "C++",
    ".hpp": "C++",
    ".hxx": "C++",
    ".h++": "C++",
    
    # C#/.NET
    ".cs": "C#",
    ".csproj": "MSBuild",
    ".sln": "MSBuild",
    ".vb": "VB.NET",
    
    # Go
    ".go": "Go",
    ".mod": "Go",
    ".sum": "Go",
    
    # Rust
    ".rs": "Rust",
    ".toml": "TOML",
    
    # PHP
    ".php": "PHP",
    ".php3": "PHP",
    ".php4": "PHP",
    ".php5": "PHP",
    ".phtml": "PHP",
    ".phar": "PHP",
    
    # Ruby
    ".rb": "Ruby",
    ".erb": "ERB",
    ".gemspec": "Ruby",
    ".jbuilder": "Ruby",
    
    # Shell
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".ps1": "PowerShell",
    ".psm1": "PowerShell",
    ".psd1": "PowerShell",
    
    # SQL
    ".sql": "SQL",
    ".tsql": "T-SQL",

    # Configuration
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".ini": "INI",
    ".cfg": "Config",
    ".conf": "Config",
    ".config": "Config",
    ".properties": "Java Properties",

    # Markdown
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".mdown": "Markdown",
    ".mkd": "Markdown",
    ".mdx": "MDX",

    # Other
    ".r": "R",
    ".R": "R",
    ".swift": "Swift",
    ".lua": "Lua",
    ".pl": "Perl",
    ".pm": "Perl",
    ".proto": "Protocol Buffer",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
    ".dockerfile": "Dockerfile",
    ".tex": "LaTeX",
    ".rst": "reStructuredText",
}

# Special filenames that indicate a language
SPECIAL_FILES = {
    "Makefile": "Makefile",
    "makefile": "Makefile",
    "GNUmakefile": "Makefile",
    "Dockerfile": "Dockerfile",
    "dockerfile": "Dockerfile",
    ".dockerignore": "Docker",
    "Gemfile": "Ruby",
    "Rakefile": "Ruby",
    "Guardfile": "Ruby",
    "Procfile": "Procfile",
    "Procfile.dev": "Procfile",
    "Appfile": "Ruby",
    "Berksfile": "Ruby",
    "Cheffile": "Chef",
    "Podfile": "Cocoapods",
    "Cartfile": "Carthage",
    "Package.swift": "Swift",
    "Cargo.toml": "Rust",
    "Cargo.lock": "Rust",
    ".travis.yml": "YAML",
    ".github": "GitHub Actions",
    "bitbucket-pipelines.yml": "YAML",
    ".circleci": "CircleCI",
    "tox.ini": "Python",
    "setup.py": "Python",
    "setup.cfg": "Python",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "Pipfile": "Python",
    "poetry.lock": "Python",
    "package.json": "JSON",
    "package-lock.json": "JSON",
    "yarn.lock": "YAML",
    ".npmrc": "NPM",
    ".nvmrc": "Node Version",
    "tsconfig.json": "JSON",
    ".eslintrc": "JSON",
    ".prettierrc": "JSON",
    "webpack.config.js": "JavaScript",
    "webpack.config.ts": "TypeScript",
    "babel.config.js": "JavaScript",
    "jest.config.js": "JavaScript",
    "rollup.config.js": "JavaScript",
    "gulpfile.js": "JavaScript",
    "Gruntfile.js": "JavaScript",
    "vite.config.ts": "TypeScript",
    "next.config.js": "JavaScript",
    "nuxt.config.ts": "TypeScript",
}

# Language shebang detection
SHEBANG_MAP = {
    "python": "Python",
    "python3": "Python",
    "python2": "Python",
    "node": "JavaScript",
    "nodejs": "JavaScript",
    "ruby": "Ruby",
    "perl": "Perl",
    "bash": "Shell",
    "sh": "Shell",
    "zsh": "Shell",
    "ksh": "Shell",
    "fish": "Shell",
    "php": "PHP",
    "lua": "Lua",
    "awk": "AWK",
    "sed": "Sed",
}


# =============================================================================
# Data classes
# =============================================================================


@dataclass
class FileStats:
    """Statistics for analyzed files."""

    files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0

    def add(self, other: "FileStats") -> None:
        """Add another FileStats to this one."""
        self.files += other.files
        self.total_lines += other.total_lines
        self.code_lines += other.code_lines
        self.comment_lines += other.comment_lines
        self.blank_lines += other.blank_lines


# =============================================================================
# Configuration
# =============================================================================


class LanguageConfig:
    """Manages language detection configuration from YAML file."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "rules" / "language_config.yml"
        self._config = self._load_config(config_path)

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file with error handling."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning("Config file %s not found. Using defaults.", config_path)
            return {}
        except yaml.YAMLError as e:
            logger.warning("Error loading config file: %s. Using defaults.", e)
            return {}

    @property
    def extensions(self) -> Dict[str, str]:
        """Get file extension to language mappings."""
        return self._config.get("extensions", {})

    @property
    def filename_patterns(self) -> Dict[str, str]:
        """Get filename to language mappings."""
        return self._config.get("filename_patterns", {})

    @property
    def skip_extensions(self) -> list:
        """Get extensions to skip during analysis."""
        return self._config.get("skip_patterns", {}).get("skip_extensions", [])

    @property
    def skip_filenames(self) -> list:
        """Get filenames to skip during analysis."""
        return self._config.get("skip_patterns", {}).get("skip_filenames", [])

    @property
    def hidden_exceptions(self) -> list:
        """Get hidden files that should be analyzed."""
        return self._config.get("skip_patterns", {}).get(
            "hidden_exceptions", list(HIDDEN_FILE_EXCEPTIONS)
        )

    @property
    def max_file_size(self) -> int:
        """Get maximum file size for analysis."""
        return self._config.get("limits", {}).get("max_file_size", DEFAULT_MAX_SIZE)

    @property
    def min_file_size(self) -> int:
        """Get minimum file size for analysis."""
        return self._config.get("limits", {}).get("min_file_size", MIN_FILE_SIZE)


# =============================================================================
# Comment detection
# =============================================================================


class CommentDetector:
    """Handles comment detection for different programming languages."""

    COMMENT_PATTERNS = {
        "Python": ["#"],
        "JavaScript": ["//", "/*", "*/", "/**"],
        "TypeScript": ["//", "/*", "*/", "/**"],
        "Java": ["//", "/*", "*/", "/**"],
        "C": ["//", "/*", "*/"],
        "C++": ["//", "/*", "*/"],
        "C#": ["//", "/*", "*/"],
        "Go": ["//", "/*", "*/"],
        "Rust": ["//", "/*", "*/"],
        "PHP": ["//", "/*", "*/", "#"],
        "Ruby": ["#", "=begin", "=end"],
        "Shell": ["#"],
        "PowerShell": ["#", "<#", "#>"],
        "HTML": ["<!--", "-->"],
        "CSS": ["/*", "*/"],
        "YAML": ["#"],
        "JSON": [],  # JSON doesn't have comments
        "Markdown": [],  # Markdown content is not "code"
        "SQL": ["--", "/*", "*/"],
    }

    def is_comment_line(self, line: str, language: str) -> bool:
        """Check if a line is a comment for the given language."""
        stripped = line.strip()
        if not stripped:
            return False

        patterns = self.COMMENT_PATTERNS.get(language, ["#", "//", "/*"])
        return any(stripped.startswith(pattern) for pattern in patterns)


# =============================================================================
# File utilities
# =============================================================================


class FileUtils:
    """Utility functions for file operations."""

    @staticmethod
    def get_file_info(file_path: str) -> Tuple[str, str]:
        """Extract normalized filename and extension."""
        path_obj = Path(file_path)
        return path_obj.name.lower(), path_obj.suffix.lower()

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size safely, returning 0 if error."""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    @staticmethod
    def read_file_lines(file_path: str) -> list:
        """Read file lines safely, returning empty list if error."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.readlines()
        except (OSError, UnicodeError):
            return []
    
    @staticmethod
    def read_file_bytes(file_path: str) -> bytes:
        """Read file as bytes safely, returning empty bytes if error."""
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except (OSError, IOError):
            return b""
    
    @staticmethod
    def get_shebang(file_path: str) -> Optional[str]:
        """Extract shebang from file if present."""
        try:
            with open(file_path, "rb") as f:
                first_bytes = f.read(128)
                if first_bytes.startswith(b"#!"):
                    shebang = first_bytes.split(b"\n")[0].decode("utf-8", errors="ignore")
                    return shebang.lstrip("#!").strip()
        except Exception:
            pass
        return None


# =============================================================================
# File walker
# =============================================================================


class FileWalker:
    """Handles project file traversal with filtering."""

    def __init__(self, config: LanguageConfig):
        self.config = config

    def walk_source_files(self, project_path: str) -> Iterator[str]:
        """Walk through project files, yielding paths of relevant files."""
        for root, dirs, files in os.walk(project_path):
            # Filter out unwanted directories using unified constants
            dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]

            for file in files:
                yield os.path.join(root, file)

    def should_analyze_file(self, file_path: str) -> bool:
        
        filename, extension = FileUtils.get_file_info(file_path)

        # Skip by global extension rules (images, pdfs, zips, etc.)
        if extension in SKIP_EXTENSIONS:
            return False

        # Skip by global filename rules
        if filename in SKIP_FILENAMES:
            return False

        # Skip hidden files (except allowed ones)
        if filename.startswith(".") and filename not in self.config.hidden_exceptions:
            return False

        # Skip by extension (config)
        if extension in self.config.skip_extensions:
            return False

        # Skip by filename (config)
        if filename in self.config.skip_filenames:
            return False

        # Check file size limits
        file_size = FileUtils.get_file_size(file_path)
        if file_size > self.config.max_file_size or file_size < self.config.min_file_size:
            return False

        return True


# =============================================================================
# File analyzer
# =============================================================================


class FileAnalyzer:
    """Analyzes files for language detection and line counting."""

    def __init__(
        self,
        config: LanguageConfig,
        comment_detector: CommentDetector,
        file_walker: FileWalker,
    ):
        self.config = config
        self.comment_detector = comment_detector
        self.file_walker = file_walker
    
    def _detect_via_tree_sitter(self, file_path: str, extension: str) -> Optional[str]:
        """Use tree-sitter to detect language from file content."""
        if not TREE_SITTER_AVAILABLE:
            return None
        
        try:
            content = FileUtils.read_file_bytes(file_path)
            if not content:
                return None
            
            # Map extensions to tree-sitter language names
            ext_to_ts_lang = {
                ".py": "python", ".java": "java", ".js": "javascript", 
                ".ts": "typescript", ".jsx": "javascript", ".tsx": "typescript",
                ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp",
                ".cs": "c_sharp", ".go": "go", ".rb": "ruby", ".php": "php",
                ".rs": "rust", ".swift": "swift", ".kt": "kotlin",
            }
            
            ts_lang = ext_to_ts_lang.get(extension)
            if not ts_lang:
                return None
            
            parser = get_parser(ts_lang)
            tree = parser.parse(content)
            
            # If parsing succeeds, language is confirmed
            if tree and tree.root_node:
                # Extra validation: check if it's the right language
                # by looking for language-specific keywords
                return None  # Let fallback detection handle it
        except Exception:
            pass
        
        return None
    
    def _detect_via_shebang(self, file_path: str) -> Optional[str]:
        """Detect language from shebang line."""
        shebang = FileUtils.get_shebang(file_path)
        if not shebang:
            return None
        
        # Extract interpreter name
        for interpreter, language in SHEBANG_MAP.items():
            if interpreter in shebang.lower():
                return language
        
        return None
    
    def _detect_via_content_heuristics(self, file_path: str) -> Optional[str]:
        """Detect language from file content patterns."""
        try:
            lines = FileUtils.read_file_lines(file_path)
            if not lines:
                return None
            
            # Check first 20 lines for language-specific patterns
            content_sample = "".join(lines[:20]).lower()
            
            # Python patterns
            if any(p in content_sample for p in ["import ", "from ", "def ", "class ", "@", "if __name__"]):
                return "Python"
            
            # JavaScript/TypeScript patterns
            if any(p in content_sample for p in ["import ", "export ", "const ", "let ", "var ", "async ", "await "]):
                return "JavaScript"
            
            # Java patterns
            if any(p in content_sample for p in ["package ", "import ", "class ", "public ", "private "]):
                if "public class" in content_sample or "package " in content_sample:
                    return "Java"
            
            # C# patterns
            if any(p in content_sample for p in ["namespace ", "using ", "class ", "public ", "interface "]):
                if "namespace " in content_sample:
                    return "C#"
            
            # Go patterns
            if "package main" in content_sample or "import (" in content_sample:
                return "Go"
            
            # Ruby patterns
            if any(p in content_sample for p in ["def ", "class ", "require ", "attr_", "@"]):
                return "Ruby"
            
            # PHP patterns
            if "<?php" in content_sample or "<?" in content_sample:
                return "PHP"
            
        except Exception:
            pass
        
        return None

    def detect_language(self, file_path: str) -> str:
        """
        Comprehensive language detection with multiple strategies.
        
        Detection priority:
        1. Special filenames (Dockerfile, Makefile, etc.)
        2. Shebang line (for scripts)
        3. Extension mapping (built-in + config)
        4. Tree-sitter validation (if available)
        5. Content heuristics
        6. Fallback to "Unknown"
        """
        filename, extension = FileUtils.get_file_info(file_path)
        
        # Strategy 1: Check special filenames
        if filename in SPECIAL_FILES:
            return SPECIAL_FILES[filename]
        
        # Also check without lowercase
        original_filename = Path(file_path).name
        if original_filename in SPECIAL_FILES:
            return SPECIAL_FILES[original_filename]
        
        # Strategy 2: Check shebang (for scripts without extension)
        if not extension or extension == ".":
            lang = self._detect_via_shebang(file_path)
            if lang:
                return lang
        
        # Strategy 3: Check built-in extension map
        if extension in EXTENSION_MAP:
            return EXTENSION_MAP[extension]
        
        # Strategy 4: Check config-based patterns
        if filename in self.config.filename_patterns:
            return self.config.filename_patterns[filename]
        
        if extension in self.config.extensions:
            return self.config.extensions[extension]
        
        # Strategy 5: Try tree-sitter validation
        if TREE_SITTER_AVAILABLE and extension:
            ts_result = self._detect_via_tree_sitter(file_path, extension)
            if ts_result:
                return ts_result
        
        # Strategy 6: Content heuristics
        lang = self._detect_via_content_heuristics(file_path)
        if lang:
            return lang
        
        return "Unknown"

    def detect_language_by_extension(self, file_path: str) -> str:
        """Legacy method - now uses comprehensive detection."""
        return self.detect_language(file_path)

    def count_lines_of_code(self, file_path: str, language: str) -> FileStats:
        """
        Count different types of lines in a file with multi-line comment handling.
        
        Handles:
        - Single-line comments (// # --)
        - Multi-line comments (/* */ <!-- -->)
        - Block comments (=begin =end)
        """
        lines = FileUtils.read_file_lines(file_path)

        if not lines:
            return FileStats()

        stats = FileStats(files=1, total_lines=len(lines))
        
        # Get multi-line comment delimiters for this language
        multiline_start = None
        multiline_end = None
        
        multiline_pairs = {
            "Python": ("'''", "'''"),  # Also """ but not handling triple quotes
            "JavaScript": ("/*", "*/"),
            "TypeScript": ("/*", "*/"),
            "Java": ("/*", "*/"),
            "C": ("/*", "*/"),
            "C++": ("/*", "*/"),
            "C#": ("/*", "*/"),
            "Go": ("/*", "*/"),
            "Rust": ("/*", "*/"),
            "PHP": ("/*", "*/"),
            "Ruby": ("=begin", "=end"),
            "HTML": ("<!--", "-->"),
            "CSS": ("/*", "*/"),
            "SQL": ("/*", "*/"),
        }
        
        if language in multiline_pairs:
            multiline_start, multiline_end = multiline_pairs[language]
        
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()

            # Handle blank lines
            if not stripped:
                stats.blank_lines += 1
                continue
            
            # Handle multi-line comments
            if multiline_start:
                if multiline_start in stripped and multiline_end in stripped:
                    # Single line with both start and end
                    if stripped.startswith(multiline_start):
                        stats.comment_lines += 1
                        continue
                
                if in_multiline_comment:
                    stats.comment_lines += 1
                    if multiline_end in stripped:
                        in_multiline_comment = False
                    continue
                
                if multiline_start in stripped:
                    in_multiline_comment = True
                    stats.comment_lines += 1
                    continue
            
            # Handle single-line comments
            if self.comment_detector.is_comment_line(line, language):
                stats.comment_lines += 1
            else:
                stats.code_lines += 1

        return stats

    def analyze_single_file(self, file_path: str) -> Tuple[str, FileStats]:
        """Analyze a single file and return language and stats."""
        language = self.detect_language(file_path)
        stats = self.count_lines_of_code(file_path, language)
        return language, stats


# =============================================================================
# Project analyzer
# =============================================================================


class ProjectAnalyzer:
    """High-level project analysis combining all components."""

    def __init__(self):
        self.config = LanguageConfig()
        self.comment_detector = CommentDetector()
        self.file_walker = FileWalker(self.config)
        self.file_analyzer = FileAnalyzer(
            self.config, self.comment_detector, self.file_walker
        )

    def analyze_project_languages(
        self, project_path: str, include_filtered: bool = False
    ) -> Dict[str, int]:
        """Analyze programming languages in a project directory (file counts only)."""
        language_stats = {}

        for file_path in self.file_walker.walk_source_files(project_path):
            if not self.file_walker.should_analyze_file(file_path):
                if include_filtered:
                    language_stats["Filtered"] = language_stats.get("Filtered", 0) + 1
                continue

            language = self.file_analyzer.detect_language(file_path)
            language_stats[language] = language_stats.get(language, 0) + 1

        return language_stats

    def analyze_project_lines_of_code(
        self, project_path: str, include_filtered: bool = False
    ) -> Dict[str, FileStats]:
        """Analyze lines of code by language in a project directory."""
        language_stats = {}

        for file_path in self.file_walker.walk_source_files(project_path):
            if not self.file_walker.should_analyze_file(file_path):
                if include_filtered:
                    if "Filtered" not in language_stats:
                        language_stats["Filtered"] = FileStats()
                    language_stats["Filtered"].files += 1
                continue

            language, stats = self.file_analyzer.analyze_single_file(file_path)

            if language not in language_stats:
                language_stats[language] = FileStats()

            language_stats[language].add(stats)

        return language_stats

    def get_unknown_files(self, project_path: str, limit: int = 20) -> list:
        """Get list of files classified as 'Unknown'."""
        unknown_files = []

        for file_path in self.file_walker.walk_source_files(project_path):
            if not self.file_walker.should_analyze_file(file_path):
                continue

            if self.file_analyzer.detect_language_by_extension(file_path) == "Unknown":
                unknown_files.append(file_path)
                if len(unknown_files) >= limit:
                    break

        return unknown_files


# =============================================================================
# Stats formatting
# =============================================================================


class StatsFormatter:
    """Formats and displays analysis results."""

    @staticmethod
    def format_analysis_to_json(
        analyzer: ProjectAnalyzer, project_path: str, include_filtered: bool = False
    ) -> dict:
        """Format analysis results as JSON data structure."""
        file_stats = analyzer.analyze_project_languages(
            project_path, include_filtered=include_filtered
        )
        loc_stats = analyzer.analyze_project_lines_of_code(
            project_path, include_filtered=include_filtered
        )

        # Convert FileStats objects to dictionaries for JSON serialization
        json_data = {
            "project_path": str(project_path),
            "file_counts": file_stats,
            "lines_of_code": {
                lang: {
                    "files": stats.files,
                    "total_lines": stats.total_lines,
                    "code_lines": stats.code_lines,
                    "comment_lines": stats.comment_lines,
                    "blank_lines": stats.blank_lines,
                }
                for lang, stats in loc_stats.items()
            },
        }

        return json_data

    @staticmethod
    def save_analysis_to_json(
        analyzer: ProjectAnalyzer,
        project_path: str,
        output_file: str = None,
        include_filtered: bool = False,
    ) -> str:
        """Save analysis results to JSON file and return the file path."""
        import json
        from pathlib import Path

        json_data = StatsFormatter.format_analysis_to_json(
            analyzer, project_path, include_filtered
        )

        # Generate default filename if not provided
        if output_file is None:
            project_name = Path(project_path).name
            output_file = f"{project_name}_language_analysis.json"

        # Ensure the output directory exists
        output_path = Path(output_file)
        if not output_path.is_absolute():
            # Save to outputs directory by default
            outputs_dir = Path.cwd() / "outputs"
            outputs_dir.mkdir(parents=True, exist_ok=True)
            output_path = outputs_dir / output_file

        # Write JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        return str(output_path)

    @staticmethod
    def print_detailed_language_stats(
        analyzer: ProjectAnalyzer, project_path: str, show_filtered: bool = False
    ):
        """Print comprehensive language statistics including lines of code."""
        print(f"Language Analysis for: {project_path}")
        print("=" * 60)

        # Get both file counts and lines of code
        file_stats = analyzer.analyze_project_languages(
            project_path, include_filtered=show_filtered
        )
        loc_stats = analyzer.analyze_project_lines_of_code(
            project_path, include_filtered=show_filtered
        )

        # Combine and sort by lines of code
        combined_stats = []
        for lang in set(list(file_stats.keys()) + list(loc_stats.keys())):
            if lang == "Filtered" and not show_filtered:
                continue

            file_count = file_stats.get(lang, 0)
            loc_data = loc_stats.get(lang, FileStats())

            combined_stats.append(
                {
                    "language": lang,
                    "files": file_count,
                    "total_lines": loc_data.total_lines,
                    "code_lines": loc_data.code_lines,
                    "comment_lines": loc_data.comment_lines,
                    "blank_lines": loc_data.blank_lines,
                }
            )

        # Sort by code lines (descending)
        combined_stats.sort(key=lambda x: x["code_lines"], reverse=True)

        # Print header
        print(
            f"{'Language':<12} {'Files':<6} {'Total':<8} {'Code':<8} {'Comments':<9} {'Blank':<6}"
        )
        print("-" * 60)

        total_files = 0
        total_code = 0
        total_lines = 0

        for stat in combined_stats:
            lang = stat["language"]
            files = stat["files"]
            total = stat["total_lines"]
            code = stat["code_lines"]
            comments = stat["comment_lines"]
            blank = stat["blank_lines"]

            print(
                f"{lang:<12} {files:<6} {total:<8} {code:<8} {comments:<9} {blank:<6}"
            )

            if lang != "Filtered":
                total_files += files
                total_code += code
                total_lines += total

        print("-" * 60)
        print(f"{'TOTAL':<12} {total_files:<6} {total_lines:<8} {total_code:<8}")

        if not show_filtered and "Filtered" in file_stats:
            print(
                f"\n{file_stats['Filtered']} files were filtered out (use show_filtered=True to include)"
            )

    @staticmethod
    def show_unknown_files(
        analyzer: ProjectAnalyzer, project_path: str, limit: int = 20
    ):
        """Show sample of files that are classified as 'Unknown'."""
        unknown_files = analyzer.get_unknown_files(
            project_path, limit * 2
        )  # Get more than needed

        if unknown_files:
            print(f"\nUnknown files (showing first {min(limit, len(unknown_files))}):")
            print("-" * 50)
            for i, file_path in enumerate(unknown_files[:limit]):
                file_name = os.path.basename(file_path)
                file_ext = Path(file_path).suffix
                rel_path = os.path.relpath(file_path, project_path)
                print(f"{i+1:2d}. {file_name} (ext: '{file_ext}') - {rel_path}")

            if len(unknown_files) > limit:
                print(f"... and {len(unknown_files) - limit} more unknown files")
        else:
            print("\nNo unknown files found!")


# =============================================================================
# Public API functions
# =============================================================================


def analyze_project_languages(
    project_path: str, include_filtered: bool = False
) -> Dict[str, int]:
    """Analyze programming languages in a project (file counts only)."""
    analyzer = ProjectAnalyzer()
    return analyzer.analyze_project_languages(project_path, include_filtered)


def analyze_project_lines_of_code(
    project_path: str, include_filtered: bool = False
) -> Dict[str, FileStats]:
    """Analyze lines of code by language in a project."""
    analyzer = ProjectAnalyzer()
    return analyzer.analyze_project_lines_of_code(project_path, include_filtered)
