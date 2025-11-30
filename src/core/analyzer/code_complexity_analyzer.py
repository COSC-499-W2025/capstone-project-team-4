from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional

from tree_sitter_languages import get_parser

# Language / grammar mappings

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
        "loop_nodes": {"for_statement", "enhanced_for_statement", "while_statement", "do_statement"},
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


@dataclass
class FunctionMetrics:
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



# Parser helpers


_PARSER_CACHE: Dict[str, object] = {}


def _get_parser_for_language(lang_name: str):

    if lang_name not in _PARSER_CACHE:
        _PARSER_CACHE[lang_name] = get_parser(lang_name)
    return _PARSER_CACHE[lang_name]


def _detect_language_from_extension(path: Path) -> Optional[str]:
    return EXT_TO_LANG.get(path.suffix.lower())


def _get_spec_for_language(language: str) -> Optional[Dict[str, set]]:
    return LANGUAGE_SPECS.get(language)


def _get_function_name(node) -> str:
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return name_node.text.decode("utf-8", errors="ignore")
    return "<anonymous>"


def _calculate_cyclomatic(node, spec) -> int:
    complexity = 1
    stack = [node]
    branch_count = 0
    loop_count = 0

    branch_nodes = spec["branch_nodes"]
    loop_nodes = spec["loop_nodes"]

    while stack:
        n = stack.pop()
        if n.type in branch_nodes:
            branch_count += 1
            complexity += 1
        elif n.type in loop_nodes:
            loop_count += 1
            complexity += 1
        stack.extend(n.children)
    
    if branch_count > 0 or loop_count > 0:
        print(f"      🔀 Found {branch_count} branches, {loop_count} loops")
    
    return complexity


def _is_method(node, spec) -> bool:
    containers = spec["method_container_nodes"]
    parent = node.parent
    while parent is not None:
        if parent.type in containers:
            return True
        parent = parent.parent
    return False



def _max_loop_depth(node, spec) -> int:
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

def analyze_file(path: Path) -> List[FunctionMetrics]:
    print(f"🔍 Starting complexity analysis for: {path.name}")
    
    language = _detect_language_from_extension(path)
    if not language:
        print(f"⚠️  No language detected for extension: {path.suffix}")
        return []

    print(f"📝 Detected language: {language}")
    
    spec = _get_spec_for_language(language)
    if not spec:
        print(f"❌ No language specification found for: {language}")
        return []
    
    print(f"📋 Using specification with {len(spec['function_nodes'])} function node types")

    parser_name = LANG_TO_PARSER_NAME.get(language)
    if not parser_name:
        print(f"❌ No parser name mapping for: {language}")
        return []

    print(f"🔧 Initializing parser: {parser_name}")
    parser = _get_parser_for_language(parser_name)
    source = path.read_bytes()
    tree = parser.parse(source)
    root = tree.root_node
    print(f"🌳 AST parsed successfully, root node type: {root.type}")

    results: List[FunctionMetrics] = []
    stack = [root]
    nodes_processed = 0
    functions_found = 0
    
    print(f"🔎 Starting AST traversal to find functions...")

    while stack:
        node = stack.pop()
        nodes_processed += 1
        
        # Progress reporting every 100 nodes
        if nodes_processed % 100 == 0:
            print(f"  📊 Processed {nodes_processed} nodes, found {functions_found} functions")

        if node.type in spec["function_nodes"]:
            functions_found += 1
            func_name = _get_function_name(node)
            print(f"  🎯 Analyzing function: '{func_name}' (type: {node.type})")

            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            length_lines = max(1, end_line - start_line + 1)
            print(f"    📏 Lines {start_line}-{end_line} ({length_lines} lines)")

            complexity = _calculate_cyclomatic(node, spec)
            complexity_per_10 = complexity * 10.0 / length_lines
            print(f"    🧮 Cyclomatic complexity: {complexity} (per 10 lines: {complexity_per_10:.2f})")

            is_method = _is_method(node, spec)
            loop_depth = _max_loop_depth(node, spec)
            print(f"    🔗 Method: {is_method}, Max loop depth: {loop_depth}")

            results.append(
                FunctionMetrics(
                    file_path=str(path),
                    name=func_name,
                    start_line=start_line,
                    end_line=end_line,
                    cyclomatic_complexity=complexity,
                    length_lines=length_lines,
                    complexity_per_10_lines=complexity_per_10,
                    is_method=is_method,
                    max_loop_depth=loop_depth,
                )
            )

        stack.extend(node.children)

    print(f"✅ Complexity analysis complete:")
    print(f"  📊 Total nodes processed: {nodes_processed}")
    print(f"  🎯 Functions analyzed: {len(results)}")
    if results:
        avg_complexity = sum(f.cyclomatic_complexity for f in results) / len(results)
        max_complexity = max(f.cyclomatic_complexity for f in results)
        print(f"  📈 Average complexity: {avg_complexity:.2f}")
        print(f"  🔥 Maximum complexity: {max_complexity}")
    print(f"")
    
    return results



def analyze_python_file(path: Path) -> List[FunctionMetrics]: # Backwards-compatible helper used elsewhere in the project. Internally just calls analyze_file.
    print(f"🐍 Using Python-specific analyzer (legacy wrapper)")
    return analyze_file(path)
