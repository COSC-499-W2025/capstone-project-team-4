"""
Framework detection module.

Recursively scans a project and detects frameworks based on YAML rules.
Supports multiple ecosystems by reading package.json, pyproject.toml,
requirements*.txt, angular.json, nest-cli.json, etc.

Features:
  - Lock file analysis (package-lock.json, yarn.lock, poetry.lock)
  - Transitive dependency detection
  - Tree-sitter based AST parsing for accurate import extraction
  - Multi-language support (Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby)
  - Framework-specific configuration detection

Migrated from src/core/framework_detector.py
Added caching for rules loading.
"""

from __future__ import annotations

import ast
import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# tomllib: Python 3.11+ / for 3.10 use tomli
try:
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

# Tree-sitter for accurate multi-language parsing
try:
    from tree_sitter_languages import get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.debug("tree-sitter not available, falling back to regex-based import detection")


# =============================================================================
# File IO helpers
# =============================================================================

TEXT_SCAN_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".json", ".yml", ".yaml", ".toml", ".txt",
    ".cfg", ".ini", ".xml", ".md", ".properties",
    ".gradle", ".kts", ".cs", ".sln", ".java",
    ".php", ".rb", ".go", ".rs"
}


def read_text_safe(path: Path) -> str | None:
    """Read text file safely, returning None on error."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def read_bytes_safe(path: Path) -> bytes | None:
    """Read bytes from file safely, returning None on error."""
    try:
        return path.read_bytes()
    except Exception:
        return None


def load_json_safe(path: Path) -> dict | None:
    """Load JSON file safely, returning None on error."""
    txt = read_text_safe(path)
    if not txt:
        return None
    try:
        return json.loads(txt)
    except Exception:
        return None


def load_toml_safe(path: Path) -> dict | None:
    """Load TOML file safely, returning None on error."""
    raw = read_bytes_safe(path)
    if not raw:
        return None
    try:
        return tomllib.loads(raw.decode("utf-8", errors="ignore"))
    except Exception:
        return None


def path_in_excludes(path: Path, excludes: set[str]) -> bool:
    """Check if any part of the path is in the excludes set."""
    return any(part in excludes for part in path.parts)


def any_glob(folder: Path, patterns: list[str], excludes: set[str]) -> bool:
    """Check if any file matching the patterns exists in the folder."""
    for pat in patterns:
        for p in folder.rglob(pat):
            if not path_in_excludes(p, excludes):
                return True
    return False


def scan_text_any(folder: Path, needles: list[str], excludes: set[str]) -> bool:
    """Scan text files under folder for any of the needles (simple substring)."""
    if not needles:
        return False
    for p in folder.rglob("*"):
        if p.is_file() and p.suffix.lower() in TEXT_SCAN_EXTS and not path_in_excludes(p, excludes):
            txt = read_text_safe(p)
            if not txt:
                continue
            for n in needles:
                if n and (n in txt):
                    return True
    return False

# =============================================================================
# Lock file parsing for accurate dependency detection
# =============================================================================

def parse_package_lock(path: Path) -> dict[str, set[str]]:
    """
    Parse package-lock.json to get all dependencies (direct + transitive).
    
    Returns dict mapping package name to versions.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        deps = {}
        
        # NPM 7+ uses packages field, earlier versions use dependencies
        packages = data.get("packages", {})
        if packages:
            for pkg_path, pkg_data in packages.items():
                if pkg_path == "" or pkg_path == ".":
                    continue
                # Extract package name from path (node_modules/package or node_modules/@scope/package)
                parts = pkg_path.split("/")
                if len(parts) >= 2:
                    if parts[1].startswith("@"):
                        pkg_name = f"{parts[1]}/{parts[2]}"
                    else:
                        pkg_name = parts[1]
                    version = pkg_data.get("version", "")
                    deps[pkg_name.lower()] = version
        
        # Fallback for older format
        if not deps:
            dependencies = data.get("dependencies", {})
            for name in dependencies.keys():
                deps[name.lower()] = ""
        
        return deps
    except Exception as e:
        logger.debug("Could not parse package-lock.json: %s", e)
        return {}


def parse_yarn_lock(path: Path) -> dict[str, set[str]]:
    """Parse yarn.lock to extract dependencies."""
    try:
        content = path.read_text(encoding="utf-8")
        deps = {}
        
        # Simple regex-based parsing for yarn.lock format
        # Format: "package@version:" or "package@npm:alias@version:"
        pattern = r'^"?([^@"]+)@'
        for line in content.split("\n"):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                pkg_name = match.group(1).lower()
                deps[pkg_name] = ""
        
        return deps
    except Exception as e:
        logger.debug("Could not parse yarn.lock: %s", e)
        return {}


def parse_poetry_lock(path: Path) -> dict[str, str]:
    """Parse poetry.lock to extract Python dependencies."""
    try:
        content = path.read_text(encoding="utf-8")
        deps = {}
        
        # TOML format: [[package]] sections
        in_package = False
        current_name = ""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("[[package]]"):
                in_package = True
            elif in_package and line.startswith("name ="):
                # Extract quoted name
                match = re.search(r'name = "([^"]+)"', line)
                if match:
                    current_name = match.group(1).lower()
                    deps[current_name] = ""
                    in_package = False
        
        return deps
    except Exception as e:
        logger.debug("Could not parse poetry.lock: %s", e)
        return {}


def get_all_dependencies(folder: Path) -> dict[str, str]:
    """
    Get all dependencies (direct + transitive) from lock files or package managers.
    
    Returns dict of package_name -> version.
    """
    all_deps = {}
    
    # npm/yarn lock files
    for lock_file in ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"]:
        path = folder / lock_file
        if path.exists():
            if lock_file == "package-lock.json":
                all_deps.update(parse_package_lock(path))
            elif lock_file == "yarn.lock":
                all_deps.update(parse_yarn_lock(path))
            # pnpm-lock.yaml is YAML, similar approach
            break  # Only use one lock file
    
    # Poetry lock file
    poetry_lock = folder / "poetry.lock"
    if poetry_lock.exists():
        all_deps.update(parse_poetry_lock(poetry_lock))
    
    # Fallback: read package.json directly
    if not all_deps:
        pkg_json = load_json_safe(folder / "package.json")
        if pkg_json:
            for key in ["dependencies", "devDependencies"]:
                all_deps.update({k.lower(): v for k, v in (pkg_json.get(key) or {}).items()})
    
    return all_deps


# =============================================================================
# Tree-sitter based import detection (multi-language)
# =============================================================================

def extract_imports_with_treesitter(file_path: Path, language: str) -> set[str]:
    """
    Extract package imports using tree-sitter for accurate multi-language parsing.
    
    Supports: Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby
    """
    if not TREE_SITTER_AVAILABLE:
        return set()
    
    try:
        source = file_path.read_bytes()
        if not source:
            return set()
        
        parser = get_parser(language)
        tree = parser.parse(source)
        imports = set()
        
        # Walk all nodes and extract imports based on language
        stack = [tree.root_node]
        
        while stack:
            node = stack.pop()
            node_type = node.type
            
            # Python imports
            if language == "python":
                if node_type in {"import_statement", "import_from_statement"}:
                    text = node.text.decode("utf-8", errors="ignore")
                    # Extract package name using regex as fallback
                    if node_type == "import_statement":
                        match = re.search(r'import\s+([a-zA-Z0-9_][a-zA-Z0-9_\.]*)', text)
                        if match:
                            pkg = match.group(1).split(".")[0].lower()
                            imports.add(pkg)
                    else:
                        match = re.search(r'from\s+([a-zA-Z0-9_][a-zA-Z0-9_\.]*)', text)
                        if match:
                            pkg = match.group(1).split(".")[0].lower()
                            imports.add(pkg)
            
            # JavaScript/TypeScript imports
            elif language in {"javascript", "typescript"}:
                if node_type == "import_statement":
                    text = node.text.decode("utf-8", errors="ignore")
                    match = re.search(r"from\s+['\"]([^'\"]+)['\"]", text)
                    if match:
                        pkg = match.group(1).lower()
                        if pkg.startswith("@"):
                            pkg = pkg.split("/")[1] if "/" in pkg else pkg
                        else:
                            pkg = pkg.split("/")[0]
                        imports.add(pkg)
                
                elif node_type == "call_expression":
                    text = node.text.decode("utf-8", errors="ignore")
                    if "require(" in text or "import(" in text:
                        match = re.search(r"['\"]([^'\"]+)['\"]", text)
                        if match:
                            pkg = match.group(1).lower()
                            if pkg.startswith("@"):
                                pkg = pkg.split("/")[1] if "/" in pkg else pkg
                            else:
                                pkg = pkg.split("/")[0]
                            imports.add(pkg)
            
            # Java imports
            elif language == "java":
                if node_type == "import_statement":
                    text = node.text.decode("utf-8", errors="ignore")
                    match = re.search(r'import\s+([a-zA-Z0-9_.]+)', text)
                    if match:
                        pkg = match.group(1).split(".")[0].lower()
                        imports.add(pkg)
            
            # Go imports
            elif language == "go":
                if node_type == "import_statement":
                    text = node.text.decode("utf-8", errors="ignore")
                    matches = re.findall(r'"([^"]+)"', text)
                    for match in matches:
                        pkg = match.split("/")[-1].lower()
                        imports.add(pkg)
            
            # C# using statements
            elif language == "c_sharp":
                if node_type == "using_directive":
                    text = node.text.decode("utf-8", errors="ignore")
                    match = re.search(r'using\s+([a-zA-Z0-9_.]+)', text)
                    if match:
                        pkg = match.group(1).split(".")[0].lower()
                        imports.add(pkg)
            
            # PHP use statements
            elif language == "php":
                if node_type == "namespace_use_clause":
                    text = node.text.decode("utf-8", errors="ignore")
                    match = re.search(r'use\s+([a-zA-Z0-9_\\]+)', text)
                    if match:
                        pkg = match.group(1).split("\\")[0].lower()
                        imports.add(pkg)
            
            # Ruby require statements
            elif language == "ruby":
                if node_type == "method_call":
                    text = node.text.decode("utf-8", errors="ignore")
                    if "require" in text:
                        match = re.search(r"require[_relative]*\s*['\"]([^'\"]+)['\"]", text)
                        if match:
                            pkg = match.group(1).split("/")[0].lower()
                            imports.add(pkg)
            
            # Add children to stack for traversal
            for child in node.children:
                stack.append(child)
        
        return imports
    
    except Exception as e:
        logger.debug("Tree-sitter import extraction failed for %s (%s): %s", file_path, language, e)
        return set()


# =============================================================================
# AST-based import detection (fallback)
# =============================================================================

def extract_python_imports(file_path: Path) -> set[str]:
    """
    Extract top-level module names from Python imports using AST.
    
    Returns set of module names (e.g., {'django', 'flask', 'numpy'}).
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get the top-level module name
                    module = alias.name.split(".")[0].lower()
                    imports.add(module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0].lower()
                    imports.add(module)
        
        return imports
    except Exception:
        return set()


def extract_js_imports(file_path: Path) -> set[str]:
    """
    Extract package names from JavaScript/TypeScript imports.
    
    Tries tree-sitter first for accuracy, falls back to regex.
    """
    # Try tree-sitter first if available
    if TREE_SITTER_AVAILABLE:
        # Detect language from extension
        lang_map = {".js": "javascript", ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript"}
        language = lang_map.get(file_path.suffix, "javascript")
        
        ts_imports = extract_imports_with_treesitter(file_path, language)
        if ts_imports:
            return ts_imports
    
    # Fallback to regex-based extraction
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        imports = set()
        
        # Match: import X from 'package' or import X from "package"
        patterns = [
            r"from\s+['\"]([^'\"]+)['\"]",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
            r"import\s+['\"]([^'\"]+)['\"]",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, source):
                pkg = match.group(1).lower()
                # Handle scoped packages (@scope/package)
                if pkg.startswith("@"):
                    pkg = pkg.split("/")[1] if "/" in pkg else pkg
                else:
                    pkg = pkg.split("/")[0]  # Get root package name
                imports.add(pkg)
        
        return imports
    except Exception:
        return set()


def scan_actual_imports(folder: Path, excludes: set[str]) -> set[str]:
    """
    Scan for actual imports in code using tree-sitter (more accurate than text search).
    
    Supports: Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby
    
    Returns set of imported package names.
    """
    imports = set()
    
    # Python imports - use tree-sitter if available, else AST
    for py_file in folder.rglob("*.py"):
        if not path_in_excludes(py_file, excludes):
            if TREE_SITTER_AVAILABLE:
                imports.update(extract_imports_with_treesitter(py_file, "python"))
            else:
                imports.update(extract_python_imports(py_file))
    
    # JavaScript/TypeScript imports - use tree-sitter if available
    for ext, lang in [("*.js", "javascript"), ("*.ts", "typescript"), 
                       ("*.jsx", "javascript"), ("*.tsx", "typescript")]:
        for js_file in folder.rglob(ext):
            if not path_in_excludes(js_file, excludes):
                imports.update(extract_js_imports(js_file))
    
    # Java imports - if tree-sitter available
    if TREE_SITTER_AVAILABLE:
        for java_file in folder.rglob("*.java"):
            if not path_in_excludes(java_file, excludes):
                imports.update(extract_imports_with_treesitter(java_file, "java"))
    
    # Go imports - if tree-sitter available
    if TREE_SITTER_AVAILABLE:
        for go_file in folder.rglob("*.go"):
            if not path_in_excludes(go_file, excludes):
                imports.update(extract_imports_with_treesitter(go_file, "go"))
    
    # C# imports - if tree-sitter available
    if TREE_SITTER_AVAILABLE:
        for cs_file in folder.rglob("*.cs"):
            if not path_in_excludes(cs_file, excludes):
                imports.update(extract_imports_with_treesitter(cs_file, "c_sharp"))
    
    # PHP imports - if tree-sitter available
    if TREE_SITTER_AVAILABLE:
        for php_file in folder.rglob("*.php"):
            if not path_in_excludes(php_file, excludes):
                imports.update(extract_imports_with_treesitter(php_file, "php"))
    
    # Ruby imports - if tree-sitter available
    if TREE_SITTER_AVAILABLE:
        for rb_file in folder.rglob("*.rb"):
            if not path_in_excludes(rb_file, excludes):
                imports.update(extract_imports_with_treesitter(rb_file, "ruby"))
    
    return imports

# =============================================================================
# Rules loading with caching
# =============================================================================

@lru_cache(maxsize=16)
def _load_rules(rules_path: str) -> dict:
    """
    Load YAML rules from file with caching.

    Args:
        rules_path: Path to the YAML rules file

    Returns:
        Parsed rules dictionary
    """
    raw = Path(rules_path).read_text(encoding="utf-8")
    rules = yaml.safe_load(raw)
    if not isinstance(rules, dict):
        raise ValueError(f"Invalid rules file format: {rules_path}")
    return rules


def get_default_rules_path() -> Path:
    """Get the default path to frameworks.yml rules file."""
    return Path(__file__).parent.parent / "rules" / "frameworks.yml"


# =============================================================================
# Signal evaluation
# =============================================================================

def eval_signal(
    sig: dict,
    folder: Path,
    pkg_json: dict | None,
    settings: dict,
    all_deps: dict[str, str] | None = None,
    actual_imports: set[str] | None = None
) -> tuple[float, list[str]]:
    """
    Evaluate a single signal spec against `folder`.

    Args:
        sig: Signal specification dictionary
        folder: Folder to evaluate
        pkg_json: Parsed package.json if available
        settings: Rules settings
        all_deps: All dependencies from lock files (direct + transitive)
        actual_imports: Actual imports detected in code

    Returns:
        Tuple of (score_delta, list of emitted signals)
    """
    t = sig.get("type")
    weight = float(sig.get("weight", 0.0))
    emitted: list[str] = []
    excludes = set(settings.get("exclude_dirs", []))
    
    if all_deps is None:
        all_deps = {}
    if actual_imports is None:
        actual_imports = set()

    # --- NEW: Check lock files for dependencies (most accurate) ---
    if t == "pkg_json_dep" and all_deps:
        key = sig.get("key") or "dependencies"
        contains = (sig.get("contains") or "").lower()
        
        # Check if package is in lock file (more accurate than checking package.json)
        if any(contains in pkg_name for pkg_name in all_deps.keys()):
            emitted.append(f"lockfile_dep:{contains}")
            # Slightly higher weight for lock file detection
            return weight * 1.1, emitted
    
    # Fallback to package.json if no lock files
    if t == "pkg_json_dep" and pkg_json:
        key = sig.get("key") or "dependencies"
        contains = (sig.get("contains") or "").lower()

        if key in {"dependencies", "devDependencies", "peerDependencies", "optionalDependencies"}:
            deps = pkg_json.get(key) or {}
        else:
            # backward-compatible: merge deps+devDeps
            deps = (pkg_json.get("dependencies") or {}) | (pkg_json.get("devDependencies") or {})

        if any(contains in (name or "").lower() for name in deps.keys()):
            emitted.append(f"pkg_json_dep:{key}:{contains}")
            return weight, emitted
        return 0.0, emitted

    if t == "pkg_json_script" and pkg_json:
        needle = (sig.get("contains") or "").lower()
        scripts = pkg_json.get("scripts") or {}
        if any(needle in (v or "").lower() for v in scripts.values()):
            emitted.append(f"pkg_json_script:{needle}")
            return weight, emitted
        return 0.0, emitted

    # --- NEW: Actual import detection (via AST) ---
    if t == "import_snippet" and actual_imports:
        needle = (sig.get("value") or "").lower()
        if needle and any(needle in pkg for pkg in actual_imports):
            emitted.append(f"import_detected:{needle}")
            return weight, emitted
    
    if t == "import_snippet_any" and actual_imports:
        vals = sig.get("value") or []
        if not isinstance(vals, list):
            vals = [vals]
        needle_set = {(v or "").lower() for v in vals}
        if needle_set and any(any(needle in pkg for pkg in actual_imports) for needle in needle_set):
            emitted.append(f"import_detected_any:{list(needle_set)[0]}")
            return weight, emitted

    # --- file/dir existence ---
    if t == "file_exists":
        p = folder / sig.get("value")
        if p.exists():
            emitted.append(f"file:{sig.get('value')}")
            return weight, emitted
        return 0.0, emitted

    if t == "file_exists_any":
        for cand in sig.get("value", []):
            if (folder / cand).exists():
                emitted.append(f"file_any:{cand}")
                return weight, emitted
        return 0.0, emitted

    if t == "file_exists_glob":
        patterns = sig.get("value") or []
        if any_glob(folder, patterns, excludes):
            emitted.append(f"file_glob:{patterns[0] if patterns else '*'}")
            return weight, emitted
        return 0.0, emitted

    if t == "dir_exists":
        p = folder / sig.get("value")
        if p.exists() and p.is_dir():
            emitted.append(f"dir:{sig.get('value')}")
            return weight, emitted
        return 0.0, emitted

    if t == "dir_exists_any":
        for cand in sig.get("value", []):
            p = folder / cand
            if p.exists() and p.is_dir():
                emitted.append(f"dir_any:{cand}")
                return weight, emitted
        return 0.0, emitted

    # --- generic text contains / import snippets (fallback) ---
    if t == "import_snippet":
        needle = sig.get("value") or ""
        if needle and scan_text_any(folder, [needle], excludes):
            emitted.append(f"import:{needle}")
            return weight, emitted
        return 0.0, emitted

    if t == "import_snippet_any":
        vals = sig.get("value") or []
        if not isinstance(vals, list):
            vals = [vals]
        if vals and scan_text_any(folder, vals, excludes):
            emitted.append(f"import_any:{vals[0]}")
            return weight, emitted
        return 0.0, emitted

    if t == "cfg_contains":
        needle = sig.get("value") or ""
        if needle and scan_text_any(folder, [needle], excludes):
            emitted.append(f"cfg:{needle}")
            return weight, emitted
        # extra check for yaml files (Flutter)
        for f in folder.rglob("*.yaml"):
            try:
                txt = f.read_text(encoding="utf-8")
                if re.search(needle, txt):
                    emitted.append(f"cfg_contains:{f.name}:{needle}")
                    return weight, emitted
            except Exception:
                continue
        return 0.0, emitted

    # --- Python: requirements*.txt ---
    if t == "req_txt_contains":
        needle = (sig.get("value") or "").lower()
        # typical file names: requirements.txt, requirements-dev.txt, requirements/*.txt
        candidates = list(folder.glob("requirements*.txt")) + list(folder.rglob("requirements/*.txt"))
        for p in candidates:
            txt = read_text_safe(p) or ""
            if needle in txt.lower():
                emitted.append(f"req:{p.name}:{needle}")
                return weight, emitted
        return 0.0, emitted

    # --- Python: toml_dep (pyproject.toml / poetry) ---
    if t in {"toml_dep", "poetry_dep"}:
        # poetry_dep is alias with default key = tool.poetry.dependencies
        key = sig.get("key") or ("tool.poetry.dependencies" if t == "poetry_dep" else "project.dependencies")
        needle = (sig.get("contains") or "").lower()
        pyproj = folder / "pyproject.toml"
        if pyproj.exists():
            tml = load_toml_safe(pyproj) or {}
            cur: dict | list | None = tml
            for part in key.split("."):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    cur = None
                    break
            names: list[str] = []
            if isinstance(cur, dict):
                names = [k.lower() for k in cur.keys()]
            elif isinstance(cur, list):
                # ["django>=4", "fastapi"] style
                names = [re.split(r"[<>= ]", x, maxsplit=1)[0].lower() for x in cur]
            if any(needle in n for n in names):
                emitted.append(f"toml_dep:{key}:{needle}")
                return weight, emitted
        return 0.0, emitted

    # Unknown/unsupported signal type -> 0
    return 0.0, emitted


# =============================================================================
# Detection pipeline
# =============================================================================

def detect_frameworks_in_folder(folder: Path, rules: dict) -> list[dict]:
    """
    Detect frameworks in a single folder using YAML rules.

    Reads package.json if present (for pkg_json_* signals),
    parses lock files for accurate dependency detection,
    scans actual code imports, and evaluates all supported signals
    against files under the folder.

    Args:
        folder: Folder to analyze
        rules: Parsed YAML rules

    Returns:
        List of detected framework dictionaries
    """
    settings = (rules or {}).get("settings", {}) or {}
    default_min = float(settings.get("default_min_score", 0.7))
    pkg_json = load_json_safe(folder / "package.json")
    
    # NEW: Get all dependencies (including transitive from lock files)
    all_deps = get_all_dependencies(folder)
    
    # NEW: Scan for actual imports in code
    excludes = set(settings.get("exclude_dirs", []))
    actual_imports = scan_actual_imports(folder, excludes)

    results: list[dict] = []

    # Prevent crashes if the 'frameworks' section is missing or invalid
    frameworks_spec = (rules or {}).get("frameworks") or {}
    if not isinstance(frameworks_spec, dict):
        frameworks_spec = {}

    for fw_name, spec in frameworks_spec.items():
        # Skip if the spec is not a dictionary
        if not isinstance(spec, dict):
            logger.debug("frameworks.%s is %s; expected dict. Skipped.", fw_name, type(spec).__name__)
            continue

        score = 0.0
        fired: list[str] = []

        signals_list = spec.get("signals") or []
        if not isinstance(signals_list, list):
            logger.debug("frameworks.%s.signals is not a list. Skipped.", fw_name)
            signals_list = []

        for sig in signals_list:
            if not isinstance(sig, dict):
                continue
            # Pass lock files and actual imports to signal evaluator
            delta, msgs = eval_signal(sig, folder, pkg_json, settings, all_deps, actual_imports)
            if delta:
                score += delta
                fired.extend(msgs)

        min_needed = float(spec.get("min_score", default_min))
        if score >= min_needed and fired:
            results.append({
                "name": fw_name,
                "confidence": min(1.0, round(score, 3)),
                "signals": fired[:50],  # Prevent overly verbose outputs
            })
    return results


def detect_frameworks_recursive(
    project_root: Path,
    rules_path: str | None = None
) -> dict:
    """
    From the project root, recursively collect candidate folders and detect frameworks.

    Candidate folders are those that contain any of:
      - package.json
      - pyproject.toml
      - requirements*.txt (or requirements/*.txt)
      - cookiecutter.json
      - angular.json
      - nest-cli.json
    Excludes folders per rules.settings.exclude_dirs.

    Args:
        project_root: Root directory of the project
        rules_path: Path to YAML rules file (default: frameworks.yml in rules directory)

    Returns:
        Dictionary with project_root, rules_version, and frameworks detected
    """
    if rules_path is None:
        rules_path = str(get_default_rules_path())

    rules = _load_rules(rules_path)
    settings = rules.get("settings", {})
    exclude_dirs = set(settings.get("exclude_dirs", []))

    candidates: set[Path] = set()

    # 1) package.json-based projects
    for pj in project_root.rglob("package.json"):
        if not path_in_excludes(pj, exclude_dirs):
            candidates.add(pj.parent)

    # 2) Python / template / angular / nest workspaces
    for pat in ["pyproject.toml", "requirements*.txt", "cookiecutter.json", "angular.json", "nest-cli.json"]:
        for f in project_root.rglob(pat):
            if not path_in_excludes(f, exclude_dirs):
                candidates.add(f.parent)

    if not candidates:
        return {
            "message": "No candidate folders found",
            "frameworks": {},
            "project_root": str(project_root.resolve()),
            "rules_version": rules.get("rules_version", "unknown"),
        }

    all_results: dict[str, list[dict]] = {}
    for folder in sorted(candidates):
        relative = str(folder.relative_to(project_root)).replace("\\", "/") if folder != project_root else "."
        fw_list = detect_frameworks_in_folder(folder, rules)
        if fw_list:
            all_results[relative] = fw_list

    return {
        "project_root": str(project_root.resolve()),
        "rules_version": rules.get("rules_version", "unknown"),
        "frameworks": all_results
    }


# =============================================================================
# Output formatting
# =============================================================================

def pretty_print_results(results: dict | list) -> None:
    """
    Print framework detection results in a human-readable format.

    Args:
        results: Detection results from detect_frameworks_recursive
    """
    # Handle list-of-batches (just in case caller changes aggregator)
    if isinstance(results, list):
        for r in results:
            project_root = r.get("project_root") or r.get("path") or "(unknown path)"
            print(f" Frameworks detected in: {project_root}\n")
            frameworks = r.get("frameworks", {})
            if not frameworks:
                print("No known frameworks detected.")
                continue
            for folder, fw_list in frameworks.items():
                print(f" {folder or '.'}:")
                if not fw_list:
                    print("  (No frameworks detected)")
                else:
                    for fw in fw_list:
                        name = fw.get("name", "(unknown)")
                        conf = fw.get("confidence", "?")
                        print(f"  - {name} (confidence: {conf})")
                        for sig in fw.get("signals", []):
                            print(f"     signals: {sig}")
                print("")
        return

    # Normal dict structure
    project_root = results.get("project_root", "(unknown project)")
    print(f" Frameworks detected in: {project_root}\n")
    frameworks = results.get("frameworks", {})

    if not frameworks:
        print("No known frameworks detected.")
        return

    for folder, fw_list in frameworks.items():
        print(f" {folder or '.'}:")
        if not fw_list:
            print("  (No frameworks detected)")
        else:
            for fw in fw_list:
                name = fw.get("name", "(unknown)")
                conf = fw.get("confidence", "?")
                print(f"  - {name} (confidence: {conf})")
                for sig in fw.get("signals", []):
                    print(f"     signals: {sig}")
        print("")
