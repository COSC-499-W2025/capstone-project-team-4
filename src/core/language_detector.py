import os
import yaml
from pathlib import Path
from typing import Dict, Any, Iterator, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class FileStats:
    """Statistics for analyzed files."""
    files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    def add(self, other: 'FileStats') -> None:
        """Add another FileStats to this one."""
        self.files += other.files
        self.total_lines += other.total_lines
        self.code_lines += other.code_lines
        self.comment_lines += other.comment_lines
        self.blank_lines += other.blank_lines


class Constants:
    """Configuration constants."""
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
            config_path = Path(__file__).parent / "language_config.yml"
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


class FileWalker:
    """Handles project file traversal with filtering."""
    
    def __init__(self, config: LanguageConfig):
        self.config = config
    
    def walk_source_files(self, project_path: str) -> Iterator[str]:
        """Walk through project files, yielding paths of relevant files."""
        for root, dirs, files in os.walk(project_path):
            # Filter out unwanted directories
            dirs[:] = [d for d in dirs if d not in Constants.SKIP_DIRECTORIES]
            
            for file in files:
                yield os.path.join(root, file)
    
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

class FileAnalyzer:
    """Analyzes files for language detection and line counting."""
    
    def __init__(self, config: LanguageConfig, comment_detector: CommentDetector, file_walker: FileWalker):
        self.config = config
        self.comment_detector = comment_detector
        self.file_walker = file_walker
    
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
    
    def count_lines_of_code(self, file_path: str, language: str) -> FileStats:
        """Count different types of lines in a file."""
        lines = FileUtils.read_file_lines(file_path)
        
        if not lines:
            return FileStats()
        
        stats = FileStats(files=1, total_lines=len(lines))
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                stats.blank_lines += 1
            elif self.comment_detector.is_comment_line(line, language):
                stats.comment_lines += 1
            else:
                stats.code_lines += 1
        
        return stats
    
    def analyze_single_file(self, file_path: str) -> Tuple[str, FileStats]:
        """Analyze a single file and return language and stats."""
        language = self.detect_language_by_extension(file_path)
        stats = self.count_lines_of_code(file_path, language)
        return language, stats

class ProjectAnalyzer:
    """High-level project analysis combining all components."""
    
    def __init__(self):
        self.config = LanguageConfig()
        self.comment_detector = CommentDetector()
        self.file_walker = FileWalker(self.config)
        self.file_analyzer = FileAnalyzer(self.config, self.comment_detector, self.file_walker)
    
    def analyze_project_languages(self, project_path: str, include_filtered: bool = False) -> Dict[str, int]:
        """Analyze programming languages in a project directory (file counts only)."""
        language_stats = {}
        
        for file_path in self.file_walker.walk_source_files(project_path):
            if not self.file_walker.should_analyze_file(file_path):
                if include_filtered:
                    language_stats['Filtered'] = language_stats.get('Filtered', 0) + 1
                continue
            
            language = self.file_analyzer.detect_language_by_extension(file_path)
            language_stats[language] = language_stats.get(language, 0) + 1
        
        return language_stats
    
    def analyze_project_lines_of_code(self, project_path: str, include_filtered: bool = False) -> Dict[str, FileStats]:
        """Analyze lines of code by language in a project directory."""
        language_stats = {}
        
        for file_path in self.file_walker.walk_source_files(project_path):
            if not self.file_walker.should_analyze_file(file_path):
                if include_filtered:
                    if 'Filtered' not in language_stats:
                        language_stats['Filtered'] = FileStats()
                    language_stats['Filtered'].files += 1
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
                
            if self.file_analyzer.detect_language_by_extension(file_path) == 'Unknown':
                unknown_files.append(file_path)
                if len(unknown_files) >= limit:
                    break
        
        return unknown_files

class StatsFormatter:
    """Formats and displays analysis results."""
    
    @staticmethod
    def print_detailed_language_stats(analyzer: ProjectAnalyzer, project_path: str, show_filtered: bool = False):
        """Print comprehensive language statistics including lines of code."""
        print(f"📊 Language Analysis for: {project_path}")
        print("=" * 60)
        
        # Get both file counts and lines of code
        file_stats = analyzer.analyze_project_languages(project_path, include_filtered=show_filtered)
        loc_stats = analyzer.analyze_project_lines_of_code(project_path, include_filtered=show_filtered)
        
        # Combine and sort by lines of code
        combined_stats = []
        for lang in set(list(file_stats.keys()) + list(loc_stats.keys())):
            if lang == 'Filtered' and not show_filtered:
                continue
                
            file_count = file_stats.get(lang, 0)
            loc_data = loc_stats.get(lang, FileStats())
            
            combined_stats.append({
                'language': lang,
                'files': file_count,
                'total_lines': loc_data.total_lines,
                'code_lines': loc_data.code_lines,
                'comment_lines': loc_data.comment_lines,
                'blank_lines': loc_data.blank_lines
            })
        
        # Sort by code lines (descending)
        combined_stats.sort(key=lambda x: x['code_lines'], reverse=True)
        
        # Print header
        print(f"{'Language':<12} {'Files':<6} {'Total':<8} {'Code':<8} {'Comments':<9} {'Blank':<6}")
        print("-" * 60)
        
        total_files = 0
        total_code = 0
        total_lines = 0
        
        for stat in combined_stats:
            lang = stat['language']
            files = stat['files']
            total = stat['total_lines']
            code = stat['code_lines']
            comments = stat['comment_lines']
            blank = stat['blank_lines']
            
            print(f"{lang:<12} {files:<6} {total:<8} {code:<8} {comments:<9} {blank:<6}")
            
            if lang != 'Filtered':
                total_files += files
                total_code += code
                total_lines += total
        
        print("-" * 60)
        print(f"{'TOTAL':<12} {total_files:<6} {total_lines:<8} {total_code:<8}")
        
        if not show_filtered and 'Filtered' in file_stats:
            print(f"\n💡 {file_stats['Filtered']} files were filtered out (use show_filtered=True to include)")
    
    @staticmethod
    def show_unknown_files(analyzer: ProjectAnalyzer, project_path: str, limit: int = 20):
        """Show sample of files that are classified as 'Unknown'."""
        unknown_files = analyzer.get_unknown_files(project_path, limit * 2)  # Get more than needed
        
        if unknown_files:
            print(f"\n🔍 Unknown files (showing first {min(limit, len(unknown_files))}):")
            print("-" * 50)
            for i, file_path in enumerate(unknown_files[:limit]):
                file_name = os.path.basename(file_path)
                file_ext = Path(file_path).suffix
                rel_path = os.path.relpath(file_path, project_path)
                print(f"{i+1:2d}. {file_name} (ext: '{file_ext}') - {rel_path}")
            
            if len(unknown_files) > limit:
                print(f"... and {len(unknown_files) - limit} more unknown files")
        else:
            print(f"\n✅ No unknown files found!")

# Convenience functions for backward compatibility
def analyze_project_languages(project_path: str, include_filtered: bool = False) -> Dict[str, int]:
    """Legacy function for backward compatibility."""
    analyzer = ProjectAnalyzer()
    return analyzer.analyze_project_languages(project_path, include_filtered)

def analyze_project_lines_of_code(project_path: str, include_filtered: bool = False) -> Dict[str, FileStats]:
    """Legacy function for backward compatibility."""
    analyzer = ProjectAnalyzer()
    return analyzer.analyze_project_lines_of_code(project_path, include_filtered)

def detect_language_by_extension(file_path: str) -> str:
    """Legacy function for backward compatibility."""
    analyzer = ProjectAnalyzer()
    return analyzer.file_analyzer.detect_language_by_extension(file_path)

def should_analyze_file(file_path: str) -> bool:
    """Legacy function for backward compatibility."""
    analyzer = ProjectAnalyzer()
    return analyzer.file_walker.should_analyze_file(file_path)

def print_detailed_language_stats(project_path: str, show_filtered: bool = False):
    """Legacy function for backward compatibility."""
    analyzer = ProjectAnalyzer()
    StatsFormatter.print_detailed_language_stats(analyzer, project_path, show_filtered)

def show_unknown_files(project_path: str, limit: int = 20):
    """Legacy function for backward compatibility."""
    analyzer = ProjectAnalyzer()
    StatsFormatter.show_unknown_files(analyzer, project_path, limit)

if __name__ == "__main__":
    # Example usage with refactored classes
    project_path = '.'  # Current directory
    
    # Create analyzer instance
    analyzer = ProjectAnalyzer()
    formatter = StatsFormatter()
    
    print("📊 Detailed Language Analysis (Refactored)...")
    formatter.print_detailed_language_stats(analyzer, project_path)
    
    print("\n🔍 Checking for unknown files...")
    formatter.show_unknown_files(analyzer, project_path)
    
    print("\n📈 Including filtered files...")
    formatter.print_detailed_language_stats(analyzer, project_path, show_filtered=True)


    
