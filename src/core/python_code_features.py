from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any
import ast
import json
import requests  # <-- needed for Ollama HTTP calls


@dataclass
class LoopsInfo:
    kind: str          # 'for' or 'while'
    line_number: int
    col: int
    nesting: int       # 0 = top level, 1 = inside another loop, etc.


@dataclass
class DataStructureInfo:
    kind: str          # list_literal, dict_literal, list_comp, ...
    line_number: int
    col: int
    detail: Optional[str] = None  # e.g. "list of dicts"


@dataclass
class PythonFileFeatures:
    path: str
    ok: bool
    error: Optional[str] = None
    loops: List[LoopsInfo] | None = None
    data_structures: List[DataStructureInfo] | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "ok": self.ok,
            "error": self.error,
            "loops": [asdict(lp) for lp in (self.loops or [])],
            "data_structures": [asdict(ds) for ds in (self.data_structures or [])],
        }


class _FeatureVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.loops: List[LoopsInfo] = []
        self.data_structures: List[DataStructureInfo] = []
        self._loop_stack: List[LoopsInfo] = []

    # Loop visitors
    def visit_For(self, node: ast.For):
        self._push_loop("for", node)
        self.generic_visit(node)
        self._pop_loop()

    def visit_While(self, node: ast.While):
        self._push_loop("while", node)
        self.generic_visit(node)
        self._pop_loop()

    def _push_loop(self, kind: str, node: ast.AST):
        nesting_level = len(self._loop_stack)
        loop = LoopsInfo(
            kind=kind,
            line_number=node.lineno,
            col=getattr(node, "col_offset", 0),
            nesting=nesting_level,
        )
        self.loops.append(loop)
        self._loop_stack.append(loop)

    def _pop_loop(self):
        if self._loop_stack:
            self._loop_stack.pop()

    # Data structure visitors
    def _add_ds(self, kind: str, node: ast.AST, detail: str | None = None):
        self.data_structures.append(
            DataStructureInfo(
                kind=kind,
                line_number=node.lineno,
                col=getattr(node, "col_offset", 0),
                detail=detail,
            )
        )

    def visit_List(self, node: ast.List):
        self._add_ds("list_literal", node)
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict):
        self._add_ds("dict_literal", node)
        self.generic_visit(node)

    def visit_Set(self, node: ast.Set):
        self._add_ds("set_literal", node)
        self.generic_visit(node)

    def visit_Tuple(self, node: ast.Tuple):
        self._add_ds("tuple_literal", node)
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp):
        self._add_ds("list_comp", node)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp):
        self._add_ds("set_comp", node)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp):
        self._add_ds("dict_comp", node)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        self._add_ds("gen_exp", node)
        self.generic_visit(node)


def analyze_python_file(source: str, filename: str = "<memory>") -> PythonFileFeatures:
    # Analyze a single Python source string.
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        return PythonFileFeatures(
            path=filename,
            ok=False,
            error=str(e),
            loops=[],
            data_structures=[],
        )

    visitor = _FeatureVisitor()
    visitor.visit(tree)

    return PythonFileFeatures(
        path=filename,
        ok=True,
        error=None,
        loops=visitor.loops,
        data_structures=visitor.data_structures,
    )


def _analyze_file(path: Path) -> PythonFileFeatures:
    # Read a .py file from disk and analyze it. 
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        return PythonFileFeatures(
            path=str(path),
            ok=False,
            error=f"IOError: {e}",
            loops=[],
            data_structures=[],
        )
    return analyze_python_file(src, filename=str(path))


def analyze_python_path(root: Path | str) -> Dict[str, Any]:
   
    # Analyze all .py files under a path (file or directory) and return a summary dict suitable for feeding into Ollama.
    
    root = Path(root)
    files: list[PythonFileFeatures] = []

    if root.is_file() and root.suffix == ".py":
        files.append(_analyze_file(root))
    elif root.is_dir():
        for p in root.rglob("*.py"):
            files.append(_analyze_file(p))
    else:
        return {
            "root": str(root),
            "summary": {"ok": False, "error": "Not a .py file or directory"},
            "files": [],
        }

    total_loops = sum(len(f.loops or []) for f in files if f.ok)
    total_ds = sum(len(f.data_structures or []) for f in files if f.ok)

    max_nesting = 0
    for f in files:
        for lp in f.loops or []:
            max_nesting = max(max_nesting, lp.nesting)

    ds_counts: dict[str, int] = {}
    for f in files:
        for ds in f.data_structures or []:
            ds_counts[ds.kind] = ds_counts.get(ds.kind, 0) + 1

    return {
        "root": str(root),
        "summary": {
            "files_analyzed": len(files),
            "files_ok": sum(1 for f in files if f.ok),
            "total_loops": total_loops,
            "total_data_structures": total_ds,
            "max_loop_nesting": max_nesting,
            "data_structures_by_kind": ds_counts,
        },
        "files": [f.to_dict() for f in files],
    }


def analyze_with_ollama(
    root: Path | str,
    model: str = "llama3.1",
    max_chars_per_file: int = 6000,
) -> dict:
    
    # Combine static analysis (loops + data structures) with an Ollama summary.
    
    root = Path(root)
    struct_report = analyze_python_path(root)

    # Collect small-ish Python files as code snippets
    code_snippets: dict[str, str] = {}
    py_files: list[Path] = []

    if root.is_file() and root.suffix == ".py":
        py_files = [root]
    elif root.is_dir():
        py_files = sorted(root.rglob("*.py"))

    for p in py_files:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if not text.strip():
            continue
        if len(text) > max_chars_per_file:
            text = text[:max_chars_per_file] + "\n# [TRUNCATED]\n"
        code_snippets[str(p)] = text

    summary = struct_report.get("summary", {})

    # Build prompt for Ollama
    prompt_parts: list[str] = []
    prompt_parts.append(
    "You will receive two things:\n"
    "1. A short static analysis summary of the Python project (loops, data structures, file count, nesting).\n"
    "2. The actual source code from one or more Python files.\n\n"
    "Your job is to analyze this code like a senior software engineer.\n\n"
    "Please produce the following:\n"
    "-------------------------------\n"
    "1. **Skill Extraction**\n"
    "   - Identify the specific technical skills demonstrated by the code.\n"
    "   - Include programming concepts, libraries, tools, algorithms, and patterns.\n"
    "   - Focus ONLY on skills actually shown in the code.\n\n"
    "2. **Time Complexity Analysis**\n"
    "   - For each major function or logical block, give a clear Big-O time complexity.\n"
    "   - Explain in simple terms why that complexity makes sense.\n\n"
    "3. **Resume-Ready Project Summary**\n"
    "   - Provide 2–3 concise resume bullet points describing what this code demonstrates.\n"
    "   - Use strong action verbs and make them sound professional.\n"
    "   - Focus on technical complexity, engineering ability, automation, data handling, or design patterns.\n\n"
    "   - Quantify impact where possible (e.g., performance improvements, data size handled).\n\n"
    "4. **Do NOT hallucinate**\n"
    "   - Only extract skills or tools actually present in the code.\n"
    "   - If something is unclear, state your assumption.\n\n"
    "Format your answer cleanly using sections:\n"
    "### Skills Demonstrated\n"
    "### Time Complexity\n"
    "### Resume-Style Summary\n"
    )
    prompt_parts.append("=== STATIC ANALYSIS SUMMARY ===")
    prompt_parts.append(json.dumps(summary, indent=2))

    if code_snippets:
        prompt_parts.append("\n=== CODE SNIPPETS ===")
        for path_str, text in code_snippets.items():
            prompt_parts.append(f"\n# File: {path_str}\n")
            prompt_parts.append(text)

    full_prompt = "\n".join(prompt_parts)

    # Call local Ollama HTTP API
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": full_prompt,
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    answer = data.get("response", "").strip()

    return {
        "structure": struct_report,
        "ollama_prompt": full_prompt,
        "ollama_response": answer,
    }


if __name__ == "__main__":
    target = Path("src/core/skill_extractor.py")
    result = analyze_with_ollama(target)
    print("=== Summary ===")
    print(json.dumps(result["structure"]["summary"], indent=2))
    print("\n=== Ollama Analysis ===\n")
    print(result["ollama_response"])
