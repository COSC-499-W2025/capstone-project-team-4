# src/core/code_complexity.py

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List

from tree_sitter_languages import get_parser

@dataclass
class FunctionMetrics:
    file_path: str
    name: str
    start_line: int
    end_line: int
    cyclomatic_complexity: int

# This uses the prebuilt parser from tree_sitter_languages
PY_PARSER = get_parser("python")

def _calculate_cyclomatic(node) -> int:
    """
    Very simple cyclomatic complexity:
    Start at 1 and add 1 for each branching construct.
    """

    complexity = 1  
    stack = [node]

    while stack:
        n = stack.pop()

        # Increment on branching constructs
        if n.type in {
            "if_statement",
            "for_statement",
            "while_statement",
            "try_statement",
            "with_statement",
            "match_statement",
            "case_clause",
            "boolean_operator",
            "conditional_expression",
            "list_comprehension",
            "set_comprehension",
            "dictionary_comprehension",
        }:
            complexity += 1

        # DFS over children
        stack.extend(n.children)

    return complexity


def analyze_python_file(path: Path) -> List[FunctionMetrics]:
    """
    Parse a Python file with Tree-sitter and return per-function metrics.
    """
    source = path.read_bytes()
    tree = PY_PARSER.parse(source)
    root = tree.root_node

    results: List[FunctionMetrics] = []
    stack = [root]

    while stack:
        node = stack.pop()

        if node.type == "function_definition":
            # name field in tree-sitter python grammar
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                func_name = name_node.text.decode("utf-8", errors="ignore")
            else:
                func_name = "<anonymous>"

            start_line = node.start_point[0] + 1  # 1-based
            end_line = node.end_point[0] + 1

            complexity = _calculate_cyclomatic(node)

            results.append(
                FunctionMetrics(
                    file_path=str(path),
                    name=func_name,
                    start_line=start_line,
                    end_line=end_line,
                    cyclomatic_complexity=complexity,
                )
            )

        # Continue traversing
        stack.extend(node.children)

    return results
