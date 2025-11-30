from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Set
from pathlib import Path
import os
from ..extractor.language_parser import CommentDetector, FileUtils, LanguageDetector

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("Warning: tree-sitter not available. Falling back to regex-based analysis.")
    
try:
    from tree_sitter_languages import get_language, get_parser
    PARSERS_AVAILABLE = True
except ImportError:
    PARSERS_AVAILABLE = False
    print("Warning: tree-sitter-languages not available. Install with: pip install tree-sitter-languages")


@dataclass
class FileStats:
    """Statistics for analyzed files."""
    files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # Tree-sitter specific stats
    functions: int = 0
    classes: int = 0
    imports: int = 0
    complexity_score: float = 0.0
    
    def add(self, other: 'FileStats') -> None:
        """Add another FileStats to this one."""
        self.files += other.files
        self.total_lines += other.total_lines
        self.code_lines += other.code_lines
        self.comment_lines += other.comment_lines
        self.blank_lines += other.blank_lines
        self.functions += other.functions
        self.classes += other.classes
        self.imports += other.imports
        self.complexity_score += other.complexity_score


class TreeSitterAnalyzer:
    """Tree-sitter based code analysis for accurate parsing."""
    
    def __init__(self):
        self.parsers: Dict[str, Parser] = {}
        self.languages: Dict[str, Language] = {}
        self._initialize_parsers()
    
    def _initialize_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        if not TREE_SITTER_AVAILABLE or not PARSERS_AVAILABLE:
            return
            
        # Language names supported by tree-sitter-languages
        supported_languages = ['python', 'java', 'javascript', 'typescript', 'c', 'cpp', 'go', 'rust', 'ruby']
        
        for lang_name in supported_languages:
            try:
                # Use tree-sitter-languages for easy language/parser access
                language = get_language(lang_name)
                parser = get_parser(lang_name)
                
                # Map to our naming convention
                display_name = lang_name.title()
                if lang_name == 'cpp':
                    display_name = 'C++'
                elif lang_name == 'javascript':
                    display_name = 'JavaScript'
                elif lang_name == 'typescript':
                    display_name = 'TypeScript'
                
                self.languages[display_name] = language
                self.parsers[display_name] = parser
                    
            except Exception as e:
                print(f"Warning: Could not initialize {lang_name} parser: {e}")
    
    def is_available(self, language: str) -> bool:
        """Check if tree-sitter analysis is available for a language."""
        return language in self.parsers
    
    def analyze_syntax(self, code: str, language: str) -> Dict[str, int]:
        """Analyze code structure using tree-sitter."""
        if not self.is_available(language):
            return {}
            
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code, 'utf8'))
            root_node = tree.root_node
            
            stats = {
                'functions': 0,
                'classes': 0, 
                'imports': 0,
                'conditionals': 0,
                'loops': 0,
            }
            
            # Define node types for different languages
            node_mappings = {
                'Python': {
                    'functions': ['function_definition', 'async_function_definition'],
                    'classes': ['class_definition'],
                    'imports': ['import_statement', 'import_from_statement'],
                    'conditionals': ['if_statement'],
                    'loops': ['for_statement', 'while_statement'],
                },
                'Java': {
                    'functions': ['method_declaration', 'constructor_declaration'],
                    'classes': ['class_declaration', 'interface_declaration'],
                    'imports': ['import_declaration'],
                    'conditionals': ['if_statement'],
                    'loops': ['for_statement', 'while_statement', 'do_statement'],
                },
                'JavaScript': {
                    'functions': ['function_declaration', 'method_definition', 'arrow_function'],
                    'classes': ['class_declaration'],
                    'imports': ['import_statement'],
                    'conditionals': ['if_statement'],
                    'loops': ['for_statement', 'while_statement', 'do_statement'],
                },
                'TypeScript': {
                    'functions': ['function_declaration', 'method_definition', 'arrow_function'],
                    'classes': ['class_declaration', 'interface_declaration'],
                    'imports': ['import_statement'],
                    'conditionals': ['if_statement'],
                    'loops': ['for_statement', 'while_statement', 'do_statement'],
                },
            }
            
            if language in node_mappings:
                mappings = node_mappings[language]
                self._count_nodes_recursive(root_node, mappings, stats)
            
            return stats
            
        except Exception as e:
            print(f"Warning: Tree-sitter analysis failed for {language}: {e}")
            return {}
    
    def _count_nodes_recursive(self, node, mappings: Dict[str, list], stats: Dict[str, int]):
        """Recursively count nodes of specific types."""
        node_type = node.type
        
        for stat_name, node_types in mappings.items():
            if node_type in node_types:
                stats[stat_name] += 1
        
        # Recurse through children
        for child in node.children:
            self._count_nodes_recursive(child, mappings, stats)
    
    def extract_comments(self, code: str, language: str) -> Set[str]:
        """Extract comments using tree-sitter."""
        if not self.is_available(language):
            return set()
            
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code, 'utf8'))
            root_node = tree.root_node
            
            comments = set()
            self._extract_comments_recursive(root_node, code, comments)
            return comments
            
        except Exception as e:
            print(f"Warning: Comment extraction failed for {language}: {e}")
            return set()
    
    def _extract_comments_recursive(self, node, code: str, comments: Set[str]):
        """Recursively extract comment nodes."""
        if node.type == 'comment':
            start_byte = node.start_byte
            end_byte = node.end_byte
            comment_text = code[start_byte:end_byte]
            comments.add(comment_text.strip())
        
        for child in node.children:
            self._extract_comments_recursive(child, code, comments)


class FileAnalyzer:
    """Analyzes files for language detection and line counting with optional tree-sitter support."""
    
    def __init__(self, language_detector: LanguageDetector = None, comment_detector: CommentDetector = None, use_tree_sitter: bool = True):
        self.language_detector = language_detector or LanguageDetector()
        self.comment_detector = comment_detector or CommentDetector()
        self.use_tree_sitter = use_tree_sitter and TREE_SITTER_AVAILABLE and PARSERS_AVAILABLE
        
        if self.use_tree_sitter:
            self.tree_sitter = TreeSitterAnalyzer()
        else:
            self.tree_sitter = None
    
    def detect_language_by_extension(self, file_path: str) -> str:
        """Detect programming language based on file extension and patterns."""
        return self.language_detector.detect_language_by_extension(file_path)
    
    def count_lines_of_code(self, file_path: str, language: str) -> FileStats:
        """Count different types of lines in a file with enhanced tree-sitter analysis."""
        lines = FileUtils.read_file_lines(file_path)
        
        if not lines:
            return FileStats()
        
        stats = FileStats(files=1, total_lines=len(lines))
        code_content = ''.join(lines)
        
        # Use tree-sitter for enhanced analysis if available
        if self.tree_sitter and self.tree_sitter.is_available(language):
            try:
                # Get syntax analysis
                syntax_stats = self.tree_sitter.analyze_syntax(code_content, language)
                stats.functions = syntax_stats.get('functions', 0)
                stats.classes = syntax_stats.get('classes', 0)
                stats.imports = syntax_stats.get('imports', 0)
                
                # Calculate complexity score based on control structures
                complexity = (
                    syntax_stats.get('conditionals', 0) +
                    syntax_stats.get('loops', 0) +
                    syntax_stats.get('functions', 0)
                )
                stats.complexity_score = complexity / len(lines) * 100 if lines else 0
                
                # Extract comments using tree-sitter
                comments = self.tree_sitter.extract_comments(code_content, language)
                stats.comment_lines = len(comments)
                
                # Count code lines more accurately
                comment_line_numbers = set()
                for comment in comments:
                    # Find which lines contain comments
                    for i, line in enumerate(lines):
                        if comment.replace(' ', '').replace('\t', '') in line.replace(' ', '').replace('\t', ''):
                            comment_line_numbers.add(i)
                
                # Count lines by type
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if not stripped:
                        stats.blank_lines += 1
                    elif i in comment_line_numbers:
                        pass  # Already counted
                    else:
                        stats.code_lines += 1
                        
            except Exception as e:
                print(f"Warning: Tree-sitter analysis failed, falling back to regex: {e}")
                self._fallback_line_counting(lines, language, stats)
        else:
            # Fallback to regex-based analysis
            self._fallback_line_counting(lines, language, stats)
        
        return stats
    
    def _fallback_line_counting(self, lines: list, language: str, stats: FileStats):
        """Fallback line counting using regex patterns."""
        stats.comment_lines = 0
        stats.code_lines = 0
        stats.blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                stats.blank_lines += 1
            elif self.comment_detector.is_comment_line(line, language):
                stats.comment_lines += 1
            else:
                stats.code_lines += 1
    
    def analyze_single_file(self, file_path: str) -> Tuple[str, FileStats]:
        """Analyze a single file and return language and enhanced stats."""
        language = self.detect_language_by_extension(file_path)
        stats = self.count_lines_of_code(file_path, language)
        return language, stats
    
    def get_file_complexity(self, file_path: str) -> float:
        """Get complexity score for a single file."""
        language = self.detect_language_by_extension(file_path)
        stats = self.count_lines_of_code(file_path, language)
        return stats.complexity_score