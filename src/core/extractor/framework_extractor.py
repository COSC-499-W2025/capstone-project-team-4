from __future__ import annotations
from pathlib import Path
from fnmatch import fnmatch
from functools import lru_cache, cached_property
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import mmap
import time
import os

import json
import re

import yaml
from typing import Dict, Set, List, Tuple, Optional, Iterator

# Tree-sitter integration
try:
    from tree_sitter_languages import get_language, get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

# Import existing language detection functionality
from .language_parser import LanguageDetector, FileUtils

"""
- Recursively scans a project and detects frameworks based on YAML rules (frameworks_config.yml)
- Supports multiple ecosystems by reading package.json, pyproject.toml,
  requirements*.txt, angular.json, nest-cli.json, etc.
- Honors rules: settings.exclude_dirs, settings.default_min_score, framework.min_score
- Signal types supported (from your rules doc, subset commonly needed):
    - pkg_json_dep, pkg_json_script
    - file_exists, file_exists_any, file_exists_glob
    - dir_exists, dir_exists_any
    - import_snippet, import_snippet_any, cfg_contains
    - req_txt_contains
    - toml_dep, poetry_dep
"""

# tomllib: Python 3.11+ / for 3.10 use tomli
try:
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


# Performance configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit for text scanning
MAX_WORKERS = min(4, (os.cpu_count() or 1))  # Conservative threading
CHUNK_SIZE = 8192  # Buffer size for streaming file reads
CACHE_SIZE = 512  # LRU cache size for file operations
VERBOSE_LOGGING = False  # Disable verbose logging for performance


class TreeSitterFrameworkAnalyzer:
    """Enhanced framework detection using tree-sitter for accurate code analysis."""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        # Singleton pattern for performance
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self.parsers = {}
        self.languages = {}
        self.language_detector = LanguageDetector()
        self._initialize_parsers()
        self._initialized = True
    
    def _initialize_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        if not TREE_SITTER_AVAILABLE:
            print("⚠️  Tree-sitter not available, using fallback parsing")
            return
            
        supported_languages = ['python', 'java', 'javascript', 'typescript', 'c', 'cpp', 'go', 'rust', 'ruby']
        
        for lang_name in supported_languages:
            try:
                language = get_language(lang_name)
                parser = get_parser(lang_name)
                
                display_name = lang_name.title()
                if lang_name == 'cpp':
                    display_name = 'C++'
                elif lang_name == 'javascript':
                    display_name = 'JavaScript'
                elif lang_name == 'typescript':
                    display_name = 'TypeScript'
                
                self.languages[display_name] = language
                self.parsers[display_name] = parser
                    
            except Exception:
                continue
        
        if self.parsers:
            print(f"🔧 Tree-sitter parsers loaded: {len(self.parsers)} languages")
    
    def detect_imports(self, code: str, language: str) -> Set[str]:
        """Extract import statements using tree-sitter for accurate parsing."""
        if not TREE_SITTER_AVAILABLE or language not in self.parsers:
            return self._fallback_import_detection(code, language)
        
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code, 'utf8'))
            root_node = tree.root_node
            
            imports = set()
            self._extract_imports_recursive(root_node, code, imports, language)
            return imports
            
        except Exception:
            return self._fallback_import_detection(code, language)
    
    def _extract_imports_recursive(self, node, code: str, imports: Set[str], language: str):
        """Recursively extract import statements from AST nodes."""
        if language == 'Python':
            if node.type == 'import_statement':
                # import os, sys
                start_byte = node.start_byte
                end_byte = node.end_byte
                import_text = code[start_byte:end_byte].strip()
                imports.add(import_text)
            elif node.type == 'import_from_statement':
                # from django import settings
                start_byte = node.start_byte
                end_byte = node.end_byte
                import_text = code[start_byte:end_byte].strip()
                imports.add(import_text)
        
        elif language in ['JavaScript', 'TypeScript']:
            if node.type == 'import_statement':
                # import React from 'react'
                start_byte = node.start_byte
                end_byte = node.end_byte
                import_text = code[start_byte:end_byte].strip()
                imports.add(import_text)
        
        elif language == 'Java':
            if node.type == 'import_declaration':
                # import java.util.List
                start_byte = node.start_byte
                end_byte = node.end_byte
                import_text = code[start_byte:end_byte].strip()
                imports.add(import_text)
        
        # Recurse through children
        for child in node.children:
            self._extract_imports_recursive(child, code, imports, language)
    
    def _fallback_import_detection(self, code: str, language: str) -> Set[str]:
        """Fallback import detection using regex patterns."""
        imports = set()
        lines = code.split('\n')
        
        if language == 'Python':
            for line in lines:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    imports.add(line)
        elif language in ['JavaScript', 'TypeScript']:
            for line in lines:
                line = line.strip()
                if line.startswith('import ') and ('from' in line or line.endswith(';')):
                    imports.add(line)
        elif language == 'Java':
            for line in lines:
                line = line.strip()
                if line.startswith('import '):
                    imports.add(line)
        
        return imports
    
    def detect_framework_patterns(self, code: str, language: str, patterns: List[str]) -> List[Tuple[str, str]]:
        """Detect specific framework patterns in code using tree-sitter."""
        if not TREE_SITTER_AVAILABLE or language not in self.parsers:
            return self._fallback_pattern_detection(code, patterns)
        
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code, 'utf8'))
            root_node = tree.root_node
            
            matches = []
            for pattern in patterns:
                if self._find_pattern_in_ast(root_node, code, pattern, language):
                    matches.append((pattern, 'ast_match'))
            
            return matches
            
        except Exception:
            return self._fallback_pattern_detection(code, patterns)
    
    def _find_pattern_in_ast(self, node, code: str, pattern: str, language: str) -> bool:
        """Search for specific patterns in the AST."""
        # Check current node content
        start_byte = node.start_byte
        end_byte = node.end_byte
        node_text = code[start_byte:end_byte]
        
        if pattern.lower() in node_text.lower():
            return True
        
        # Recurse through children
        for child in node.children:
            if self._find_pattern_in_ast(child, code, pattern, language):
                return True
        
        return False
    
    def _fallback_pattern_detection(self, code: str, patterns: List[str]) -> List[Tuple[str, str]]:
        """Fallback pattern detection using simple string matching."""
        matches = []
        for pattern in patterns:
            if pattern.lower() in code.lower():
                matches.append((pattern, 'string_match'))
        return matches
    
    def get_language_from_extension(self, file_path: Path) -> Optional[str]:
        """Determine programming language from file extension using existing language detector."""
        language = self.language_detector.detect_language_by_extension(str(file_path))
        return language if language != "Unknown" else None


# =============================
# File IO helpers
# =============================

TEXT_SCAN_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".json", ".yml", ".yaml", ".toml", ".txt",
    ".cfg", ".ini", ".xml", ".md", ".properties",
    ".gradle", ".kts", ".cs", ".sln", ".java",
    ".php", ".rb", ".go", ".rs"
}

@lru_cache(maxsize=CACHE_SIZE)
def read_text_safe(path: Path) -> str | None:
    """Read text file safely with caching and size limits."""
    try:
        # Check file size first to avoid reading huge files
        stat = path.stat()
        if stat.st_size > MAX_FILE_SIZE:
            return None
        
        # Use memory mapping for large files
        if stat.st_size > CHUNK_SIZE * 4:
            with open(path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    return mm.read().decode('utf-8', errors='ignore')
        else:
            return path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError, UnicodeDecodeError):
        return None

@lru_cache(maxsize=CACHE_SIZE)
def load_json_safe(path: Path) -> dict | None:
    """Load JSON file safely with caching."""
    try:
        txt = read_text_safe(path)
        return json.loads(txt) if txt else None
    except Exception:
        return None

@lru_cache(maxsize=CACHE_SIZE)
def load_toml_safe(path: Path) -> dict | None:
    """Load TOML file safely with caching."""
    try:
        # Check file size first
        if path.stat().st_size > MAX_FILE_SIZE:
            return None
        raw = path.read_bytes()
        return tomllib.loads(raw.decode("utf-8", errors="ignore"))
    except Exception:
        return None

def path_in_excludes(path: Path, excludes: set[str]) -> bool:
    return any(part in excludes for part in path.parts)

def any_glob(folder: Path, patterns: list[str], excludes: set[str]) -> bool:
    for pat in patterns:
        for p in folder.rglob(pat):
            if not path_in_excludes(p, excludes):
                return True
    return False

def scan_text_any(folder: Path, needles: list[str], excludes: set[str], tree_analyzer: Optional[TreeSitterFrameworkAnalyzer] = None) -> bool:
    """Optimized scan with early termination, streaming, and parallel processing."""
    if not needles:
        return False
    
    if tree_analyzer is None:
        tree_analyzer = TreeSitterFrameworkAnalyzer()
    
    # Collect candidate files first (faster than checking each file individually)
    candidate_files = []
    try:
        for p in folder.rglob("*"):
            if (p.is_file() and 
                p.suffix.lower() in TEXT_SCAN_EXTS and 
                not path_in_excludes(p, excludes) and
                p.stat().st_size <= MAX_FILE_SIZE):
                candidate_files.append(p)
    except (OSError, PermissionError):
        return False
    
    if not candidate_files:
        return False
    
    # Process files in parallel for better performance
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(candidate_files))) as executor:
        future_to_file = {
            executor.submit(_scan_single_file, p, needles, tree_analyzer): p 
            for p in candidate_files
        }
        
        for future in as_completed(future_to_file):
            try:
                if future.result():  # Early termination on first match
                    return True
            except Exception:
                continue  # Skip problematic files
    
    return False


def _scan_single_file(path: Path, needles: list[str], tree_analyzer: TreeSitterFrameworkAnalyzer) -> bool:
    """Scan a single file with streaming and early termination."""
    try:
        # Use streaming for import detection patterns
        if any('import' in needle.lower() for needle in needles):
            language = tree_analyzer.get_language_from_extension(path)
            if language and TREE_SITTER_AVAILABLE:
                # Use memory-mapped file reading for tree-sitter
                with open(path, 'rb') as f:
                    if path.stat().st_size > 0:
                        try:
                            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                                content = mm.read().decode('utf-8', errors='ignore')
                                imports = tree_analyzer.detect_imports(content, language)
                                for needle in needles:
                                    if any(needle.lower() in imp.lower() for imp in imports):
                                        return True
                        except (OSError, ValueError):
                            pass  # Fall back to regular processing
        
        # Stream file content for string matching (early termination)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            buffer = ''
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                buffer += chunk
                # Check needles in current buffer
                for needle in needles:
                    if needle and needle in buffer:
                        return True
                
                # Keep last part of buffer for patterns that might span chunks
                if len(buffer) > CHUNK_SIZE:
                    buffer = buffer[-1000:]  # Keep last 1000 chars for overlap
        
        return False
        
    except (OSError, PermissionError, UnicodeDecodeError):
        return False


# =============================
# Signal evaluation
# =============================

def eval_signal(sig: dict, folder: Path, pkg_json: dict | None, settings: dict, tree_analyzer: Optional[TreeSitterFrameworkAnalyzer] = None) -> tuple[float, list[str]]:
    """
    Optimized signal evaluation with early returns and minimal processing.
    """
    t = sig.get("type")
    weight = float(sig.get("weight", 0.0))
    
    # Early return for zero-weight signals
    if weight <= 0.0:
        return 0.0, []
        
    emitted: list[str] = []
    excludes = set(settings.get("exclude_dirs", []))

    # --- package.json family ---
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

    # --- generic text contains / import snippets (enhanced with tree-sitter) ---
    if t == "import_snippet":
        needle = sig.get("value") or ""
        if needle and scan_text_any(folder, [needle], excludes, tree_analyzer):
            emitted.append(f"import:{needle}")
            return weight, emitted
        return 0.0, emitted

    if t == "import_snippet_any":
        vals = sig.get("value") or []
        if not isinstance(vals, list):
            vals = [vals]
        if vals and scan_text_any(folder, vals, excludes, tree_analyzer):
            emitted.append(f"import_any:{vals[0]}")
            return weight, emitted
        return 0.0, emitted

    if t == "cfg_contains":
        needle = sig.get("value") or ""
        if needle and scan_text_any(folder, [needle], excludes, tree_analyzer):
            emitted.append(f"cfg:{needle}")
            return weight, emitted
        # extra check for yaml files (Flutter) - optimized with file size check
        for f in folder.rglob("*.yaml"):
            try:
                if f.stat().st_size > MAX_FILE_SIZE:
                    continue
                txt = read_text_safe(f)
                if txt and re.search(needle, txt):
                    emitted.append(f"cfg_contains:{f.name}:{needle}")
                    return weight, emitted
            except Exception:
                continue
        return 0.0, emitted


    # --- Python: requirements*.txt (optimized) ---
    if t == "req_txt_contains":
        needle = (sig.get("value") or "").lower()
        if not needle:
            return 0.0, emitted
            
        # Use cached file reading and size limits
        candidates = list(folder.glob("requirements*.txt")) + list(folder.rglob("requirements/*.txt"))
        for p in candidates:
            if not path_in_excludes(p, excludes):
                txt = read_text_safe(p)
                if txt and needle in txt.lower():
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


# =============================
# Detection pipeline
# =============================

def detect_frameworks_in_folder(folder: Path, rules: dict) -> list[dict]:
    """
    Optimized framework detection with reduced logging and early termination.
    """
    settings = (rules or {}).get("settings", {}) or {}
    default_min = float(settings.get("default_min_score", 0.7))
    
    # Cache package.json loading
    pkg_json = load_json_safe(folder / "package.json")
    if VERBOSE_LOGGING and pkg_json:
        print(f"    ✅ Found package.json with {len(pkg_json.get('dependencies', {}))} dependencies")
    
    # Use singleton tree-sitter analyzer
    tree_analyzer = TreeSitterFrameworkAnalyzer() if TREE_SITTER_AVAILABLE else None

    results: list[dict] = []
    frameworks_spec = (rules or {}).get("frameworks") or {}
    if not isinstance(frameworks_spec, dict):
        return results
    
    if VERBOSE_LOGGING:
        print(f"    🔍 Testing {len(frameworks_spec)} framework definitions...")

    # Process frameworks in parallel for better performance
    framework_items = list(frameworks_spec.items())
    
    # Use threading for I/O bound framework detection
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(framework_items))) as executor:
        future_to_framework = {
            executor.submit(_detect_single_framework, fw_name, spec, folder, pkg_json, settings, tree_analyzer, default_min): fw_name
            for fw_name, spec in framework_items
        }
        
        for future in as_completed(future_to_framework):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                if VERBOSE_LOGGING:
                    fw_name = future_to_framework[future]
                    print(f"      ⚠️  Error processing {fw_name}: {e}")
    
    if VERBOSE_LOGGING:
        print(f"    🎯 Framework detection complete: {len(results)} frameworks found")
    return results


def _detect_single_framework(fw_name: str, spec: dict, folder: Path, pkg_json: dict | None, 
                           settings: dict, tree_analyzer: Optional[TreeSitterFrameworkAnalyzer], 
                           default_min: float) -> dict | None:
    """Detect a single framework with optimized processing."""
    if not isinstance(spec, dict):
        return None

    score = 0.0
    fired: list[str] = []
    signals_list = spec.get("signals") or []
    
    if not isinstance(signals_list, list):
        return None
    
    # Early termination: if we've exceeded min_score, we can stop
    min_needed = float(spec.get("min_score", default_min))
    
    for sig in signals_list:
        if not isinstance(sig, dict):
            continue
        
        delta, msgs = eval_signal(sig, folder, pkg_json, settings, tree_analyzer)
        if delta:
            score += delta
            fired.extend(msgs)
            
            # Early termination if we've already exceeded the minimum
            if score >= min_needed and len(fired) > 0:
                break
    
    if score >= min_needed and fired:
        return {
            "name": fw_name,
            "confidence": min(1.0, round(score, 3)),
            "signals": fired[:20],  # Limit signal list for performance
        }
    
    return None



@lru_cache(maxsize=16)
def _load_rules(rules_path: str) -> dict:
    """Cache rules loading for performance."""
    print(f"📋 Loading framework rules from: {Path(rules_path).name}")
    raw = Path(rules_path).read_text(encoding="utf-8")
    rules = yaml.safe_load(raw)
    if not isinstance(rules, dict):
        raise ValueError(f"Invalid rules file format: {rules_path}")
    print(f"📊 Loaded {len(rules.get('frameworks', {}))} framework definitions")
    return rules


def detect_frameworks_recursive(project_root: Path, rules_path: str) -> dict:
    """
    Optimized recursive framework detection with batch processing and parallel execution.
    """
    start_time = time.time()
    print(f"🔍 Detecting frameworks in: {project_root.name}")
    
    if VERBOSE_LOGGING:
        print(f"🔍 Starting recursive framework detection from: {project_root}")
    
    # Load and cache rules
    rules = _load_rules(rules_path)
    settings = rules.get("settings", {})
    exclude_dirs = set(settings.get("exclude_dirs", []))
    
    if VERBOSE_LOGGING:
        print(f"⚙️  Loaded {len(rules.get('frameworks', {}))} framework rules")

    # Collect candidates efficiently with single pass
    candidates = _collect_candidates_optimized(project_root, exclude_dirs)
    
    if not candidates:
        print("⚠️  No framework candidate folders found")
        return {
            "message": "No candidate folders found",
            "frameworks": {},
            "project_root": str(project_root.resolve()),
            "rules_version": rules.get("rules_version", "unknown"),
            "scan_time_seconds": round(time.time() - start_time, 2)
        }

    print(f"🔬 Processing {len(candidates)} candidates...")
    if VERBOSE_LOGGING:
        print(f"\n🔬 Processing {len(candidates)} candidates in parallel...")
    
    # Process candidates in parallel
    all_results: dict[str, list[dict]] = {}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Create relative path mapping for results
        candidate_futures = {}
        for folder in candidates:
            relative = str(folder.relative_to(project_root)).replace("\\", "/") if folder != project_root else "."
            future = executor.submit(detect_frameworks_in_folder, folder, rules)
            candidate_futures[future] = relative
        
        # Collect results as they complete
        for future in as_completed(candidate_futures):
            try:
                relative = candidate_futures[future]
                fw_list = future.result()
                if fw_list:
                    all_results[relative] = fw_list
            except Exception as e:
                if VERBOSE_LOGGING:
                    print(f"  ⚠️  Error processing candidate: {e}")
    
    scan_time = time.time() - start_time
    total_frameworks = sum(len(fw_list) for fw_list in all_results.values())
    
    print(f"✅ Found {total_frameworks} frameworks in {scan_time:.1f}s")
    if VERBOSE_LOGGING:
        print(f"\n🎉 Detection complete in {scan_time:.2f}s!")
        print(f"📊 Results: {total_frameworks} frameworks in {len(all_results)} folders")

    return {
        "project_root": str(project_root.resolve()),
        "rules_version": rules.get("rules_version", "unknown"),
        "frameworks": all_results,
        "performance_metrics": {
            "scan_time_seconds": round(scan_time, 2),
            "candidates_processed": len(candidates),
            "frameworks_found": total_frameworks,
            "avg_time_per_candidate": round(scan_time / len(candidates), 4) if candidates else 0,
            "tree_sitter_enabled": TREE_SITTER_AVAILABLE,
            "max_workers": MAX_WORKERS,
            "cache_enabled": True
        }
    }


def _collect_candidates_optimized(project_root: Path, exclude_dirs: set[str]) -> set[Path]:
    """Efficiently collect candidate folders in a single filesystem pass."""
    candidates: set[Path] = set()
    target_files = {
        "package.json", "pyproject.toml", "cookiecutter.json", 
        "angular.json", "nest-cli.json"
    }
    
    try:
        # Single walk for all file patterns
        for root, dirs, files in os.walk(project_root):
            # Filter directories in-place for performance
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            root_path = Path(root)
            
            # Check for target files
            for file in files:
                if file in target_files:
                    if not path_in_excludes(root_path, exclude_dirs):
                        candidates.add(root_path)
                        break  # No need to check other files in this directory
                elif file.startswith("requirements") and file.endswith(".txt"):
                    if not path_in_excludes(root_path, exclude_dirs):
                        candidates.add(root_path)
                        break
    
    except (OSError, PermissionError) as e:
        print(f"⚠️  Filesystem access error: {e}")
        if VERBOSE_LOGGING:
            print(f"⚠️  Filesystem access error: {e}")
    
    return candidates


def clear_performance_caches():
    """Clear all LRU caches to free memory."""
    read_text_safe.cache_clear()
    load_json_safe.cache_clear() 
    load_toml_safe.cache_clear()
    _load_rules.cache_clear()


def get_performance_stats() -> dict:
    """Get current cache performance statistics."""
    return {
        "read_text_safe_cache_info": read_text_safe.cache_info(),
        "load_json_safe_cache_info": load_json_safe.cache_info(),
        "load_toml_safe_cache_info": load_toml_safe.cache_info(),
        "load_rules_cache_info": _load_rules.cache_info(),
        "tree_sitter_available": TREE_SITTER_AVAILABLE,
        "max_workers": MAX_WORKERS,
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024)
    }