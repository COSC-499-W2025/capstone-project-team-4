import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from src.core.analyzers.language import (
    FileStats, LanguageConfig, CommentDetector, FileUtils,
    FileWalker, FileAnalyzer, ProjectAnalyzer, StatsFormatter,
    analyze_project_languages, analyze_project_lines_of_code
)
from src.core.constants import (
    SKIP_DIRECTORIES, HIDDEN_FILE_EXCEPTIONS, DEFAULT_MAX_SIZE, MIN_FILE_SIZE
)


class TestFileStats:
    """Test the FileStats dataclass."""
    
    def test_file_stats_operations(self):
        """Test FileStats initialization, values, and addition."""
        # Test default initialization
        default_stats = FileStats()
        assert all(getattr(default_stats, attr) == 0 for attr in 
                  ['files', 'total_lines', 'code_lines', 'comment_lines', 'blank_lines'])
        
        # Test with specific values
        stats = FileStats(files=5, total_lines=100, code_lines=80, comment_lines=15, blank_lines=5)
        assert (stats.files, stats.total_lines, stats.code_lines) == (5, 100, 80)
        
        # Test addition
        stats1 = FileStats(files=2, total_lines=50, code_lines=40, comment_lines=5, blank_lines=5)
        stats2 = FileStats(files=3, total_lines=75, code_lines=60, comment_lines=10, blank_lines=5)
        stats1.add(stats2)
        assert (stats1.files, stats1.total_lines, stats1.code_lines) == (5, 125, 100)


class TestConstants:
    """Test the constants module."""

    def test_constants_values(self):
        """Test that constants have expected values."""
        assert DEFAULT_MAX_SIZE == 1_000_000
        assert MIN_FILE_SIZE == 1
        expected_dirs = {'.git', '__pycache__', 'node_modules'}
        assert expected_dirs.issubset(SKIP_DIRECTORIES)
        assert '.gitignore' in HIDDEN_FILE_EXCEPTIONS


class TestLanguageConfig:
    """Test the LanguageConfig class."""
    
    @patch('builtins.open', mock_open(read_data="""
extensions:
  .py: Python
  .js: JavaScript

filename_patterns:
  dockerfile: Docker

skip_patterns:
  skip_extensions: [.exe]
  skip_filenames: [package-lock.json]

limits:
  max_file_size: 500000
  min_file_size: 5
"""))
    def test_language_config_loads_yaml(self):
        """Test LanguageConfig loads YAML configuration correctly."""
        config = LanguageConfig()
        assert config.extensions['.py'] == 'Python'
        assert config.filename_patterns['dockerfile'] == 'Docker'
        assert '.exe' in config.skip_extensions
        assert config.max_file_size == 500000
    
    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_language_config_missing_file(self, mock_file):
        """Test LanguageConfig handles missing config file gracefully."""
        config = LanguageConfig()
        assert config.extensions == {}
        assert config.filename_patterns == {}
    
    def test_language_config_yaml_error(self):
        """Test LanguageConfig handles YAML parsing errors."""
        with patch('builtins.open', mock_open(read_data="invalid: yaml: content")), \
             patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML")):
            config = LanguageConfig()
            assert config.extensions == {}
            assert config.skip_extensions == []
    
    def test_language_config_properties(self):
        """Test all LanguageConfig properties with empty config."""
        config = LanguageConfig()
        config._config = {}  # Simulate empty config

        # Test all properties return appropriate defaults
        assert config.extensions == {}
        assert config.filename_patterns == {}
        assert config.skip_extensions == []
        assert config.skip_filenames == []
        # hidden_exceptions returns a list, compare as sets
        assert set(config.hidden_exceptions) == HIDDEN_FILE_EXCEPTIONS
        assert config.max_file_size == DEFAULT_MAX_SIZE
        assert config.min_file_size == MIN_FILE_SIZE


class TestCommentDetector:
    """Test the CommentDetector class."""
    
    def test_comment_detection(self):
        """Test comment detection for various languages."""
        detector = CommentDetector()
        
        # Test patterns exist for major languages
        expected_langs = {'Python', 'JavaScript', 'Java', 'C++'}
        assert expected_langs.issubset(detector.COMMENT_PATTERNS.keys())
        
        # Test Python comments
        assert detector.is_comment_line("# This is a comment", "Python")
        assert detector.is_comment_line("    # Indented comment", "Python")
        assert not detector.is_comment_line("print('hello')", "Python")
        
        # Test JavaScript comments
        assert detector.is_comment_line("// Single line comment", "JavaScript")
        assert detector.is_comment_line("/* Block comment */", "JavaScript")
        assert not detector.is_comment_line("console.log('hello');", "JavaScript")
        
        # Test JSON has no comments
        assert not detector.is_comment_line("// This looks like comment", "JSON")
        
        # Test unknown language fallback
        assert detector.is_comment_line("# Comment", "UnknownLang")
        
        # Test edge cases
        assert not detector.is_comment_line("", "Python")  # empty line
        assert not detector.is_comment_line("   ", "Python")  # whitespace only
        assert detector.is_comment_line("   # indented", "Python")  # indented comment
        
        # Test block comment detection
        assert detector.is_comment_line("/* start */", "JavaScript")
        assert detector.is_comment_line("   /* indented */", "JavaScript")


class TestFileUtils:
    """Test the FileUtils class."""
    
    def test_get_file_info(self):
        """Test file info extraction."""
        filename, extension = FileUtils.get_file_info("/path/to/MyFile.PY")
        assert (filename, extension) == ("myfile.py", ".py")
        
        filename, extension = FileUtils.get_file_info("Dockerfile")
        assert (filename, extension) == ("dockerfile", "")
    
    @patch('os.path.getsize')
    def test_get_file_size(self, mock_getsize):
        """Test file size retrieval with success and error cases."""
        # Test success
        mock_getsize.return_value = 1024
        assert FileUtils.get_file_size("/some/file.txt") == 1024
        
        # Test error handling
        mock_getsize.side_effect = OSError("File not found")
        assert FileUtils.get_file_size("/nonexistent/file.txt") == 0
    
    @patch('builtins.open')
    def test_read_file_lines(self, mock_open_func):
        """Test file reading with success and error cases."""
        # Test success
        mock_open_func.return_value = mock_open(read_data="line 1\nline 2\n").return_value
        lines = FileUtils.read_file_lines("/some/file.txt")
        assert len(lines) == 2 and lines[0] == "line 1\n"
        
        # Test error handling
        mock_open_func.side_effect = OSError("Permission denied")
        assert FileUtils.read_file_lines("/protected/file.txt") == []
    
    def test_get_file_info_edge_cases(self):
        """Test edge cases for file info extraction."""
        # Test files with multiple dots
        filename, extension = FileUtils.get_file_info("test.backup.py")
        assert (filename, extension) == ("test.backup.py", ".py")
        
        # Test uppercase extensions
        filename, extension = FileUtils.get_file_info("FILE.JS")
        assert (filename, extension) == ("file.js", ".js")
        
        # Test path with no extension
        filename, extension = FileUtils.get_file_info("/path/to/README")
        assert (filename, extension) == ("readme", "")
        
        # Test empty filename
        filename, extension = FileUtils.get_file_info("")
        assert (filename, extension) == ("", "")


class TestFileWalker:
    """Test the FileWalker class."""
    
    def test_should_analyze_file(self):
        """Test file analysis criteria."""
        config = LanguageConfig()
        walker = FileWalker(config)
        
        # Test valid file
        with patch.object(FileUtils, 'get_file_info', return_value=('test.py', '.py')), \
             patch.object(FileUtils, 'get_file_size', return_value=1000):
            assert walker.should_analyze_file('/path/test.py')
        
        # Test hidden file (should be rejected)
        with patch.object(FileUtils, 'get_file_info', return_value=('.hidden', '')), \
             patch.object(FileUtils, 'get_file_size', return_value=1000):
            assert not walker.should_analyze_file('/path/.hidden')
        
        # Test whitelisted hidden file
        with patch.object(FileUtils, 'get_file_info', return_value=('.gitignore', '')), \
             patch.object(FileUtils, 'get_file_size', return_value=100):
            assert walker.should_analyze_file('/path/.gitignore')
        
        # Test size limits
        with patch.object(FileUtils, 'get_file_info', return_value=('large.py', '.py')):
            # Too large
            with patch.object(FileUtils, 'get_file_size', return_value=2_000_000):
                assert not walker.should_analyze_file('/path/large.py')
            # Too small 
            with patch.object(FileUtils, 'get_file_size', return_value=0):
                assert not walker.should_analyze_file('/path/large.py')
    
    def test_should_analyze_file_skip_patterns(self):
        """Test file skipping based on extensions and filenames."""
        config = LanguageConfig()
        config._config = {
            'skip_patterns': {
                'skip_extensions': ['.exe', '.dll'],
                'skip_filenames': ['package-lock.json']
            }
        }
        walker = FileWalker(config)
        
        # Test skipped extension
        with patch.object(FileUtils, 'get_file_info', return_value=('app.exe', '.exe')), \
             patch.object(FileUtils, 'get_file_size', return_value=1000):
            assert not walker.should_analyze_file('/path/app.exe')
        
        # Test skipped filename
        with patch.object(FileUtils, 'get_file_info', return_value=('package-lock.json', '.json')), \
             patch.object(FileUtils, 'get_file_size', return_value=1000):
            assert not walker.should_analyze_file('/path/package-lock.json')


@pytest.fixture
def file_analyzer():
    """Create a FileAnalyzer instance for testing."""
    config = LanguageConfig()
    comment_detector = CommentDetector()
    file_walker = FileWalker(config)
    return FileAnalyzer(config, comment_detector, file_walker)


class TestFileAnalyzer:
    """Test the FileAnalyzer class."""
    
    def test_language_detection(self, file_analyzer):
        """Test language detection by file extension and filename."""
        # Test extension match - uses built-in EXTENSION_MAP
        with patch.object(FileUtils, 'get_file_info', return_value=('script.py', '.py')):
            assert file_analyzer.detect_language_by_extension('/path/script.py') == 'Python'

        # Test filename pattern match - uses built-in SPECIAL_FILES
        with patch.object(FileUtils, 'get_file_info', return_value=('dockerfile', '')):
            assert file_analyzer.detect_language_by_extension('/path/Dockerfile') == 'Dockerfile'
    
    def test_line_counting(self, file_analyzer):
        """Test line counting for code, comments, and blanks."""
        test_content = ["# Comment\n", "def hello():\n", "    return 'world'\n", "\n"]
        
        with patch.object(FileUtils, 'read_file_lines', return_value=test_content):
            stats = file_analyzer.count_lines_of_code('/path/test.py', 'Python')
            assert (stats.files, stats.total_lines, stats.code_lines, stats.comment_lines, stats.blank_lines) == (1, 4, 2, 1, 1)
        
        # Test empty file
        with patch.object(FileUtils, 'read_file_lines', return_value=[]):
            stats = file_analyzer.count_lines_of_code('/path/empty.py', 'Python')
            assert stats.files == 0
    
    def test_analyze_single_file_integration(self, file_analyzer):
        """Test complete single file analysis workflow."""
        with patch.object(file_analyzer, 'detect_language_by_extension', return_value='Python'), \
             patch.object(file_analyzer, 'count_lines_of_code', return_value=FileStats(files=1, total_lines=10, code_lines=8)):
            
            language, stats = file_analyzer.analyze_single_file('/path/test.py')
            assert language == 'Python'
            assert stats.files == 1
            assert stats.total_lines == 10


@pytest.fixture
def project_analyzer():
    """Create a ProjectAnalyzer instance for testing."""
    return ProjectAnalyzer()


class TestProjectAnalyzer:
    """Test the ProjectAnalyzer class."""
    
    def test_analyze_project_languages(self, project_analyzer):
        """Test project language analysis (file counts only)."""
        with patch.object(project_analyzer.file_walker, 'walk_source_files', return_value=['/proj/file1.py', '/proj/file2.py', '/proj/file3.js']), \
             patch.object(project_analyzer.file_walker, 'should_analyze_file', return_value=True), \
             patch.object(project_analyzer.file_analyzer, 'detect_language_by_extension', side_effect=['Python', 'Python', 'JavaScript']):
            
            result = project_analyzer.analyze_project_languages('/project')
            assert result == {'Python': 2, 'JavaScript': 1}
    
    def test_analyze_project_lines_of_code(self, project_analyzer):
        """Test project lines of code analysis."""
        stats1 = FileStats(files=1, total_lines=50, code_lines=40, comment_lines=5, blank_lines=5)
        stats2 = FileStats(files=1, total_lines=30, code_lines=25, comment_lines=3, blank_lines=2)
        
        with patch.object(project_analyzer.file_walker, 'walk_source_files', return_value=['/proj/file1.py', '/proj/file2.py']), \
             patch.object(project_analyzer.file_walker, 'should_analyze_file', return_value=True), \
             patch.object(project_analyzer.file_analyzer, 'analyze_single_file', side_effect=[('Python', stats1), ('Python', stats2)]):
            
            result = project_analyzer.analyze_project_lines_of_code('/project')
            python_stats = result['Python']
            assert (python_stats.files, python_stats.total_lines, python_stats.code_lines) == (2, 80, 65)
    
    def test_get_unknown_files(self, project_analyzer):
        """Test unknown files detection with limit."""
        with patch.object(project_analyzer.file_walker, 'walk_source_files', return_value=['/proj/file1.xyz', '/proj/file2.abc', '/proj/file3.py']), \
             patch.object(project_analyzer.file_walker, 'should_analyze_file', return_value=True), \
             patch.object(project_analyzer.file_analyzer, 'detect_language_by_extension', side_effect=['Unknown', 'Unknown', 'Python']):
            
            unknown_files = project_analyzer.get_unknown_files('/project', limit=5)
            assert len(unknown_files) == 2
            assert all(f in unknown_files for f in ['/proj/file1.xyz', '/proj/file2.abc'])
    
    def test_analyze_empty_project(self, project_analyzer):
        """Test analyzing a project with no valid files."""
        with patch.object(project_analyzer.file_walker, 'walk_source_files', return_value=[]), \
             patch.object(project_analyzer.file_walker, 'should_analyze_file', return_value=False):
            
            # Test empty project
            result = project_analyzer.analyze_project_languages('/empty')
            assert result == {}
            
            result = project_analyzer.analyze_project_lines_of_code('/empty')
            assert result == {}
    
    def test_analyze_filtered_files(self, project_analyzer):
        """Test analyzing files with some being filtered out."""
        with patch.object(project_analyzer.file_walker, 'walk_source_files', return_value=['/proj/file1.py', '/proj/file2.exe']), \
             patch.object(project_analyzer.file_walker, 'should_analyze_file', side_effect=[True, False]), \
             patch.object(project_analyzer.file_analyzer, 'detect_language_by_extension', return_value='Python'):
            
            result = project_analyzer.analyze_project_languages('/project')
            assert result == {'Python': 1}  # Only one file should be analyzed


class TestStatsFormatter:
    """Test the StatsFormatter class."""
    
    def test_format_analysis_to_json(self):
        """Test JSON formatting of analysis results."""
        formatter = StatsFormatter()
        mock_analyzer = MagicMock()
        
        # Mock analyzer results
        file_counts = {'Python': 5, 'JavaScript': 3}
        loc_stats = {
            'Python': FileStats(files=5, total_lines=500, code_lines=400, comment_lines=50, blank_lines=50),
            'JavaScript': FileStats(files=3, total_lines=300, code_lines=250, comment_lines=25, blank_lines=25)
        }
        
        mock_analyzer.analyze_project_languages.return_value = file_counts
        mock_analyzer.analyze_project_lines_of_code.return_value = loc_stats
        
        result = formatter.format_analysis_to_json(mock_analyzer, '/project')
        
        assert result['project_path'] == '/project'
        assert result['file_counts'] == file_counts
        assert result['lines_of_code']['Python']['files'] == 5
        assert result['lines_of_code']['Python']['code_lines'] == 400
    
    def test_format_analysis_empty_results(self):
        """Test formatting when no results are found."""
        formatter = StatsFormatter()
        mock_analyzer = MagicMock()
        
        # Mock empty results
        mock_analyzer.analyze_project_languages.return_value = {}
        mock_analyzer.analyze_project_lines_of_code.return_value = {}
        
        result = formatter.format_analysis_to_json(mock_analyzer, '/empty')
        
        assert result['project_path'] == '/empty'
        assert result['file_counts'] == {}
        assert result['lines_of_code'] == {}


class TestPublicAPI:
    """Test the public API functions."""
    
    def test_public_functions(self):
        """Test public API functions delegate correctly to ProjectAnalyzer."""
        with patch('src.core.analyzers.language.ProjectAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze_project_languages.return_value = {'Python': 5}
            mock_analyzer.analyze_project_lines_of_code.return_value = {'Python': FileStats(files=5, code_lines=400)}
            
            # Test analyze_project_languages
            result1 = analyze_project_languages('/project', include_filtered=True)
            assert result1 == {'Python': 5}
            mock_analyzer.analyze_project_languages.assert_called_with('/project', True)
            
            # Test analyze_project_lines_of_code  
            result2 = analyze_project_lines_of_code('/project', include_filtered=False)
            assert result2 == {'Python': FileStats(files=5, code_lines=400)}
            mock_analyzer.analyze_project_lines_of_code.assert_called_with('/project', False)


class TestIntegration:
    """Integration tests for the language analyzer."""
    
    def test_end_to_end_analysis(self):
        """Test complete analysis workflow with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            (Path(temp_dir) / "test.py").write_text("# Comment\ndef hello():\n    return 'world'\n\n")
            (Path(temp_dir) / "test.js").write_text("// Comment\nfunction hello() { return 'world'; }")
            
            # Run analysis
            analyzer = ProjectAnalyzer()
            
            # Test file counts and lines of code
            file_counts = analyzer.analyze_project_languages(temp_dir)
            assert file_counts.get('Python') == 1
            assert file_counts.get('JavaScript') == 1
            
            loc_stats = analyzer.analyze_project_lines_of_code(temp_dir)
            if 'Python' in loc_stats:
                python_stats = loc_stats['Python']
                assert python_stats.files >= 1
                assert python_stats.code_lines >= 1
    
    def test_json_formatting(self):
        """Test JSON formatting integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "simple.py").write_text("print('hello')")
            
            analyzer = ProjectAnalyzer()
            formatter = StatsFormatter()
            json_data = formatter.format_analysis_to_json(analyzer, temp_dir)
            
            assert json_data['project_path'] == temp_dir
            assert 'file_counts' in json_data
            assert 'lines_of_code' in json_data
