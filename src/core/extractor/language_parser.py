import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class Constants:
    """Configuration constants for language detection."""
    DEFAULT_MAX_SIZE = 1_000_000  # 1MB
    DEFAULT_MIN_SIZE = 1
    
    SKIP_DIRECTORIES = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv', 
        '.pytest_cache', '.mypy_cache', '.coverage', 'htmlcov',
        'build', 'dist', '.tox', '.nox', 'target'
    }
    
    DEFAULT_HIDDEN_EXCEPTIONS = ['.gitignore', '.env', '.dockerignore']


class LanguageConfig:
    """Manages language detection configuration from YAML file."""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "language_config.yml"
        self._config = self._load_config(config_path)
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file with error handling."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Warning: Config file {config_path} not found. Using defaults.")
            return {}
        except yaml.YAMLError as e:
            print(f"Warning: Error loading config file: {e}. Using defaults.")
            return {}
    
    @property
    def extensions(self) -> Dict[str, str]:
        """Get file extension to language mappings."""
        return self._config.get('extensions', {})
    
    @property
    def filename_patterns(self) -> Dict[str, str]:
        """Get filename to language mappings."""
        return self._config.get('filename_patterns', {})
    
    @property
    def skip_extensions(self) -> list:
        """Get extensions to skip during analysis."""
        return self._config.get('skip_patterns', {}).get('skip_extensions', [])
    
    @property
    def skip_filenames(self) -> list:
        """Get filenames to skip during analysis."""
        return self._config.get('skip_patterns', {}).get('skip_filenames', [])
    
    @property
    def hidden_exceptions(self) -> list:
        """Get hidden files that should be analyzed."""
        return self._config.get('skip_patterns', {}).get('hidden_exceptions', Constants.DEFAULT_HIDDEN_EXCEPTIONS)
    
    @property
    def max_file_size(self) -> int:
        """Get maximum file size for analysis."""
        return self._config.get('limits', {}).get('max_file_size', Constants.DEFAULT_MAX_SIZE)
    
    @property
    def min_file_size(self) -> int:
        """Get minimum file size for analysis."""
        return self._config.get('limits', {}).get('min_file_size', Constants.DEFAULT_MIN_SIZE)


class CommentDetector:
    """Handles comment detection for different programming languages."""
    
    COMMENT_PATTERNS = {
        'Python': ['#'],
        'JavaScript': ['//', '/*', '*/', '/**'],
        'TypeScript': ['//', '/*', '*/', '/**'],
        'Java': ['//', '/*', '*/', '/**'],
        'C': ['//', '/*', '*/'],
        'C++': ['//', '/*', '*/'],
        'C#': ['//', '/*', '*/'],
        'Go': ['//', '/*', '*/'],
        'Rust': ['//', '/*', '*/'],
        'PHP': ['//', '/*', '*/', '#'],
        'Ruby': ['#', '=begin', '=end'],
        'Shell': ['#'],
        'PowerShell': ['#', '<#', '#>'],
        'HTML': ['<!--', '-->'],
        'CSS': ['/*', '*/'],
        'YAML': ['#'],
        'JSON': [],  # JSON doesn't have comments
        'Markdown': [],  # Markdown content is not "code"
        'SQL': ['--', '/*', '*/'],
    }
    
    def is_comment_line(self, line: str, language: str) -> bool:
        """Check if a line is a comment for the given language."""
        stripped = line.strip()
        if not stripped:
            return False
        
        patterns = self.COMMENT_PATTERNS.get(language, ['#', '//', '/*'])
        return any(stripped.startswith(pattern) for pattern in patterns)


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
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.readlines()
        except (OSError, UnicodeError):
            return []


class LanguageDetector:
    """Core language detection functionality."""
    
    def __init__(self, config: Optional[LanguageConfig] = None):
        self.config = config or LanguageConfig()
    
    def detect_language_by_extension(self, file_path: str) -> str:
        """Detect programming language based on file extension and patterns."""
        filename, extension = FileUtils.get_file_info(file_path)
        
        # First check filename patterns
        if filename in self.config.filename_patterns:
            return self.config.filename_patterns[filename]
        
        # Then check extensions
        if extension in self.config.extensions:
            return self.config.extensions[extension]
        
        return "Unknown"
    
    def should_analyze_file(self, file_path: str) -> bool:
        """Determine if a file should be analyzed."""
        filename, extension = FileUtils.get_file_info(file_path)
        
        # Skip hidden files (except allowed ones)
        if filename.startswith('.') and filename not in self.config.hidden_exceptions:
            return False
        
        # Skip by extension
        if extension in self.config.skip_extensions:
            return False
        
        # Skip by filename
        if filename in self.config.skip_filenames:
            return False
        
        # Check file size limits
        file_size = FileUtils.get_file_size(file_path)
        if file_size > self.config.max_file_size or file_size < self.config.min_file_size:
            return False
        
        return True