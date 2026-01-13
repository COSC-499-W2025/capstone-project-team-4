"""
Code complexity analysis module.

This module provides cyclomatic complexity analysis using Tree-sitter
for multiple programming languages including Python, Java, JavaScript,
TypeScript, C, C++, C#, Go, Rust, PHP, and Ruby.

Migrated from src/core/code_complexity.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional

from tree_sitter_languages import get_parser

logger = logging.getLogger(__name__)

# =============================================================================
# Language / grammar mappings
# =============================================================================

EXT_TO_LANG: Dict[str, str] = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".rb": "Ruby",
}

LANG_TO_PARSER_NAME: Dict[str, str] = {
    "Python": "python",
    "Java": "java",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "C": "c",
    "C++": "cpp",
    "C#": "c_sharp",
    "Go": "go",
    "Rust": "rust",
    "PHP": "php",
    "Ruby": "ruby",
}

# Per-language node specs: which nodes represent functions, loops, branches, etc.
LANGUAGE_SPECS: Dict[str, Dict[str, set]] = {
    "Python": {
        "function_nodes": {"function_definition"},
        "method_container_nodes": {"class_definition"},
        "loop_nodes": {"for_statement", "while_statement"},
        "branch_nodes": {
            "if_statement",
            "elif_clause",
            "match_statement",
            "case_clause",
            "try_statement",
            "with_statement",
            "boolean_operator",
            "conditional_expression",
            "list_comprehension",
            "set_comprehension",
            "dictionary_comprehension",
        },
    },
    "Java": {
        "function_nodes": {"method_declaration", "constructor_declaration"},
        "method_container_nodes": {
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
        },
        "loop_nodes": {
            "for_statement",
            "enhanced_for_statement",
            "while_statement",
            "do_statement",
        },
        "branch_nodes": {
            "if_statement",
            "switch_expression",
            "switch_block_statement_group",
            "conditional_expression",
        },
    },
    "JavaScript": {
        "function_nodes": {
            "function_declaration",
            "function",
            "method_definition",
            "arrow_function",
        },
        "method_container_nodes": {"class_declaration", "class"},
        "loop_nodes": {
            "for_statement",
            "for_in_statement",
            "for_of_statement",
            "while_statement",
            "do_statement",
        },
        "branch_nodes": {
            "if_statement",
            "switch_statement",
            "conditional_expression",
            "logical_expression",
        },
    },
    "TypeScript": {
        "function_nodes": {
            "function_declaration",
            "function",
            "method_definition",
            "arrow_function",
        },
        "method_container_nodes": {"class_declaration", "class"},
        "loop_nodes": {
            "for_statement",
            "for_in_statement",
            "for_of_statement",
            "while_statement",
            "do_statement",
        },
        "branch_nodes": {
            "if_statement",
            "switch_statement",
            "conditional_expression",
            "logical_expression",
        },
    },
    "C": {
        "function_nodes": {"function_definition"},
        "method_container_nodes": set(),  # no classes
        "loop_nodes": {"for_statement", "while_statement", "do_statement"},
        "branch_nodes": {"if_statement", "switch_statement"},
    },
    "C++": {
        "function_nodes": {"function_definition"},
        "method_container_nodes": {"class_specifier", "struct_specifier"},
        "loop_nodes": {"for_statement", "while_statement", "do_statement"},
        "branch_nodes": {"if_statement", "switch_statement"},
    },
    "C#": {
        "function_nodes": {"method_declaration", "constructor_declaration"},
        "method_container_nodes": {
            "class_declaration",
            "struct_declaration",
            "interface_declaration",
        },
        "loop_nodes": {
            "for_statement",
            "while_statement",
            "do_statement",
            "foreach_statement",
        },
        "branch_nodes": {"if_statement", "switch_statement", "conditional_expression"},
    },
    "Go": {
        "function_nodes": {"function_declaration", "method_declaration"},
        "method_container_nodes": set(),  # methods are receiver-based
        "loop_nodes": {"for_statement"},
        "branch_nodes": {
            "if_statement",
            "switch_statement",
            "type_switch_statement",
        },
    },
    "Rust": {
        "function_nodes": {"function_item"},
        "method_container_nodes": {
            "impl_item",
            "trait_item",
            "struct_item",
            "enum_item",
        },
        "loop_nodes": {
            "for_expression",
            "while_expression",
            "loop_expression",
        },
        "branch_nodes": {
            "if_expression",
            "match_expression",
        },
    },
    "PHP": {
        "function_nodes": {"function_definition", "method_declaration"},
        "method_container_nodes": {"class_declaration", "interface_declaration"},
        "loop_nodes": {
            "for_statement",
            "foreach_statement",
            "while_statement",
            "do_statement",
        },
        "branch_nodes": {
            "if_statement",
            "switch_statement",
            "conditional_expression",
        },
    },
    "Ruby": {
        "function_nodes": {"method", "singleton_method"},
        "method_container_nodes": {"class", "module"},
        "loop_nodes": {"while", "until", "for"},
        "branch_nodes": {"if", "case"},
    },
}


# =============================================================================
# Data classes
# =============================================================================


@dataclass
class FunctionMetrics:
    """Metrics for a single function or method."""

    file_path: str
    name: str
    start_line: int
    end_line: int
    cyclomatic_complexity: int
    length_lines: int
    complexity_per_10_lines: float
    is_method: bool
    max_loop_depth: int

    def as_dict(self) -> dict:
        """Convert metrics to dictionary representation."""
        return {
            "file_path": self.file_path,
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "length_lines": self.length_lines,
            "complexity_per_10_lines": round(self.complexity_per_10_lines, 2),
            "is_method": self.is_method,
            "max_loop_depth": self.max_loop_depth,
        }


# =============================================================================
# Parser helpers (with caching)
# =============================================================================

_PARSER_CACHE: Dict[str, object] = {}


def _get_parser_for_language(lang_name: str):
    """Get or create a cached parser for the given language."""
    if lang_name not in _PARSER_CACHE:
        _PARSER_CACHE[lang_name] = get_parser(lang_name)
    return _PARSER_CACHE[lang_name]


def _detect_language_from_extension(path: Path) -> Optional[str]:
    """Detect programming language from file extension."""
    return EXT_TO_LANG.get(path.suffix.lower())


def _get_spec_for_language(language: str) -> Optional[Dict[str, set]]:
    """Get language specification for AST analysis."""
    return LANGUAGE_SPECS.get(language)


def _get_function_name(node) -> str:
    """Extract function name from AST node."""
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return name_node.text.decode("utf-8", errors="ignore")
    return "<anonymous>"


def _calculate_cyclomatic(node, spec) -> int:
    """Calculate cyclomatic complexity for a function node."""
    complexity = 1
    stack = [node]

    branch_nodes = spec["branch_nodes"]
    loop_nodes = spec["loop_nodes"]

    while stack:
        n = stack.pop()
        if n.type in branch_nodes or n.type in loop_nodes:
            complexity += 1
        stack.extend(n.children)
    return complexity


def _is_method(node, spec) -> bool:
    """Check if function is a method (inside a class/struct)."""
    containers = spec["method_container_nodes"]
    parent = node.parent
    while parent is not None:
        if parent.type in containers:
            return True
        parent = parent.parent
    return False


def _max_loop_depth(node, spec) -> int:
    """Calculate maximum loop nesting depth in a function."""
    loop_nodes = spec["loop_nodes"]
    max_depth = 0
    stack = [(node, 0)]

    while stack:
        n, depth = stack.pop()

        if n.type in loop_nodes:
            max_depth = max(max_depth, depth)
            for child in n.children:
                stack.append((child, depth + 1))
        else:
            for child in n.children:
                stack.append((child, depth))

    return max_depth


# =============================================================================
# Public API
# =============================================================================


def analyze_file(path: Path) -> List[FunctionMetrics]:
    """
    Analyze a source file for function complexity metrics.

    Args:
        path: Path to the source file

    Returns:
        List of FunctionMetrics for each function/method in the file
    """
    language = _detect_language_from_extension(path)
    if not language:
        return []

    spec = _get_spec_for_language(language)
    if not spec:
        return []

    parser_name = LANG_TO_PARSER_NAME.get(language)
    if not parser_name:
        return []

    try:
        parser = _get_parser_for_language(parser_name)
        source = path.read_bytes()
        tree = parser.parse(source)
        root = tree.root_node
    except Exception as e:
        logger.warning("Could not parse file %s: %s", path, e)
        return []

    results: List[FunctionMetrics] = []
    stack = [root]

    while stack:
        node = stack.pop()

        if node.type in spec["function_nodes"]:
            func_name = _get_function_name(node)

            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            length_lines = max(1, end_line - start_line + 1)

            complexity = _calculate_cyclomatic(node, spec)
            complexity_per_10 = complexity * 10.0 / length_lines

            is_method_flag = _is_method(node, spec)
            loop_depth = _max_loop_depth(node, spec)

            results.append(
                FunctionMetrics(
                    file_path=str(path),
                    name=func_name,
                    start_line=start_line,
                    end_line=end_line,
                    cyclomatic_complexity=complexity,
                    length_lines=length_lines,
                    complexity_per_10_lines=complexity_per_10,
                    is_method=is_method_flag,
                    max_loop_depth=loop_depth,
                )
            )

        stack.extend(node.children)

    return results


def analyze_python_file(path: Path) -> List[FunctionMetrics]:
    """
    Backwards-compatible helper for analyzing Python files.

    Internally just calls analyze_file.

    Args:
        path: Path to the Python file

    Returns:
        List of FunctionMetrics for each function/method in the file
    """
    return analyze_file(path)
