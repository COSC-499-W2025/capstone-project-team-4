from __future__ import annotations
from pathlib import Path
from fnmatch import fnmatch

import json
import re

import yaml
from typing import Dict, Set, List, Tuple, Optional

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


class TreeSitterFrameworkAnalyzer:
    """Enhanced framework detection using tree-sitter for accurate code analysis."""
    
    def __init__(self):
        self.parsers = {}
        self.languages = {}
        self.language_detector = LanguageDetector()
        self._initialize_parsers()
    
    def _initialize_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        if not TREE_SITTER_AVAILABLE:
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

def read_text_safe(path: Path) -> str | None:
    """Read text file safely using existing FileUtils pattern."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

def load_json_safe(path: Path) -> dict | None:
    """Load JSON file safely."""
    try:
        txt = read_text_safe(path)
        return json.loads(txt) if txt else None
    except Exception:
        return None

def load_toml_safe(path: Path) -> dict | None:
    """Load TOML file safely."""
    try:
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
    """Scan text files under folder for any of the needles using tree-sitter when possible."""
    if not needles:
        return False
    
    if tree_analyzer is None:
        tree_analyzer = TreeSitterFrameworkAnalyzer()
    
    for p in folder.rglob("*"):
        if p.is_file() and p.suffix.lower() in TEXT_SCAN_EXTS and not path_in_excludes(p, excludes):
            # Use consistent file reading approach
            lines = FileUtils.read_file_lines(str(p))
            if not lines:
                continue
            txt = ''.join(lines)
            
            # Try tree-sitter enhanced analysis for code files
            language = tree_analyzer.get_language_from_extension(p)
            if language and TREE_SITTER_AVAILABLE:
                # Use tree-sitter for import detection if looking for import patterns
                if any('import' in needle.lower() for needle in needles):
                    imports = tree_analyzer.detect_imports(txt, language)
                    for needle in needles:
                        if any(needle.lower() in imp.lower() for imp in imports):
                            return True
                
                # Use tree-sitter for framework pattern detection
                patterns = tree_analyzer.detect_framework_patterns(txt, language, needles)
                if patterns:
                    return True
            
            # Fallback to simple string matching
            for n in needles:
                if n and (n in txt):
                    return True
    return False


# =============================
# Signal evaluation
# =============================

def eval_signal(sig: dict, folder: Path, pkg_json: dict | None, settings: dict, tree_analyzer: Optional[TreeSitterFrameworkAnalyzer] = None) -> tuple[float, list[str]]:
    """
    Evaluate a single signal spec against `folder`.
    Returns (score_delta, [emitted_signals])
    """
    t = sig.get("type")
    weight = float(sig.get("weight", 0.0))
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
            # Use consistent file reading
            lines = FileUtils.read_file_lines(str(p))
            txt = ''.join(lines)
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


# =============================
# Detection pipeline
# =============================

def detect_frameworks_in_folder(folder: Path, rules: dict) -> list[dict]:
    """
    Detect frameworks in a single folder using YAML rules with tree-sitter enhancement.
    Reads package.json if present (for pkg_json_* signals),
    and evaluates all supported signals against files under the folder.
    """
    settings = (rules or {}).get("settings", {}) or {}
    default_min = float(settings.get("default_min_score", 0.7))
    
    print(f"    📁 Loading package.json if present...")
    pkg_json = load_json_safe(folder / "package.json")
    if pkg_json:
        print(f"    ✅ Found package.json with {len(pkg_json.get('dependencies', {}))} dependencies")
    
    # Initialize tree-sitter analyzer for enhanced detection
    tree_analyzer = TreeSitterFrameworkAnalyzer() if TREE_SITTER_AVAILABLE else None
    print(f"    🌳 Tree-sitter support: {'enabled' if TREE_SITTER_AVAILABLE else 'disabled'}")

    results: list[dict] = []

    # Prevent crashes if the 'frameworks' section is missing or invalid
    frameworks_spec = (rules or {}).get("frameworks") or {}
    if not isinstance(frameworks_spec, dict):
        frameworks_spec = {}
    
    print(f"    🔍 Testing {len(frameworks_spec)} framework definitions...")

    for fw_name, spec in frameworks_spec.items():
        # ★ This was the previous crash point — skip if the spec is not a dictionary (e.g., None, string, etc.)
        if not isinstance(spec, dict):
            print(f"      ⚠️  Skipping {fw_name}: invalid spec format ({type(spec).__name__})")
            continue

        print(f"      🧪 Testing framework: {fw_name}")
        score = 0.0
        fired: list[str] = []

        signals_list = spec.get("signals") or []
        if not isinstance(signals_list, list):
            print(f"      ⚠️  {fw_name}: signals field is not a list, skipping")
            signals_list = []
        
        print(f"        📊 Evaluating {len(signals_list)} signals...")

        for i, sig in enumerate(signals_list, 1):
            if not isinstance(sig, dict):
                print(f"        ⚠️  Signal {i}: invalid format, skipping")
                continue
            
            sig_type = sig.get('type', 'unknown')
            print(f"        🔎 Signal {i}/{len(signals_list)}: {sig_type}")
            
            delta, msgs = eval_signal(sig, folder, pkg_json, settings, tree_analyzer)
            if delta:
                print(f"          ✅ Match! Score +{delta}, signals: {msgs}")
                score += delta
                fired.extend(msgs)
            else:
                print(f"          ❌ No match for {sig_type}")

        min_needed = float(spec.get("min_score", default_min))
        print(f"      📊 Final score for {fw_name}: {score:.2f} (min required: {min_needed})")
        
        if score >= min_needed and fired:
            print(f"      ✅ {fw_name} detected! Confidence: {min(1.0, round(score, 3)):.2f}")
            results.append({
                "name": fw_name,
                "confidence": min(1.0, round(score, 3)),
                "signals": fired[:50],  # Prevent overly verbose outputs
            })
        else:
            print(f"      ❌ {fw_name} not detected (score too low or no signals fired)")
    
    print(f"    🎯 Framework detection complete for folder: {len(results)} frameworks found")
    return results



def detect_frameworks_recursive(project_root: Path, rules_path: str) -> dict:
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
    """
    print(f"🔍 Starting recursive framework detection from: {project_root}")
    print(f"📋 Loading rules from: {rules_path}")
    
    raw = Path(rules_path).read_text(encoding="utf-8")
    rules = yaml.safe_load(raw) 
    if not isinstance(rules, dict):
        raise ValueError(f"Invalid rules file format: {rules_path}")
    settings = rules.get("settings", {})
    exclude_dirs = set(settings.get("exclude_dirs", []))
    
    print(f"⚙️  Loaded {len(rules.get('frameworks', {}))} framework rules")
    print(f"🚫 Excluding directories: {', '.join(sorted(exclude_dirs))}")

    candidates: set[Path] = set()
    print(f"\n🔎 Scanning for candidate project files...")

    # 1) package.json-based projects
    package_json_count = 0
    for pj in project_root.rglob("package.json"):
        package_json_count += 1
        if not path_in_excludes(pj, exclude_dirs):
            candidates.add(pj.parent)
            print(f"  📦 Found package.json candidate: {pj.parent.relative_to(project_root)}")
        else:
            print(f"  ⏭️  Skipped excluded package.json: {pj.parent.relative_to(project_root)}")
    print(f"📦 Processed {package_json_count} package.json files")

    # 2) Python / template / angular / nest workspaces
    other_patterns = ["pyproject.toml", "requirements*.txt", "cookiecutter.json", "angular.json", "nest-cli.json"]
    for pat in other_patterns:
        pattern_count = 0
        print(f"\n🔍 Searching for pattern: {pat}")
        for f in project_root.rglob(pat):
            pattern_count += 1
            if not path_in_excludes(f, exclude_dirs):
                candidates.add(f.parent)

                candidates.add(f.parent)
                print(f"  🎯 Found {pat} candidate: {f.parent.relative_to(project_root)}")
            else:
                print(f"  ⏭️  Skipped excluded {pat}: {f.parent.relative_to(project_root)}")
        print(f"✅ Found {pattern_count} {pat} files")

    print(f"\n📊 Total candidates found: {len(candidates)}")
    if not candidates:
        print("❌ No candidate folders found for framework detection")
        return {
            "message": "No candidate folders found",
            "frameworks": {},
            "project_root": str(project_root.resolve()),
            "rules_version": rules.get("rules_version", "unknown"),
        }

    print(f"\n🔬 Starting framework detection in {len(candidates)} candidate folders...")
    all_results: dict[str, list[dict]] = {}
    
    for i, folder in enumerate(sorted(candidates), 1):
        relative = str(folder.relative_to(project_root)).replace("\\", "/") if folder != project_root else "."
        print(f"\n[{i}/{len(candidates)}] 🔍 Analyzing folder: {relative}")
        
        fw_list = detect_frameworks_in_folder(folder, rules)
        if fw_list:
            framework_names = [fw['name'] for fw in fw_list]
            print(f"  ✅ Found frameworks: {', '.join(framework_names)}")
            all_results[relative] = fw_list
        else:
            print(f"  📭 No frameworks detected in this folder")
    
    total_frameworks = sum(len(fw_list) for fw_list in all_results.values())
    print(f"\n🎉 Framework detection complete!")
    print(f"📊 Results: {total_frameworks} frameworks found in {len(all_results)} folders")

    return {
        "project_root": str(project_root.resolve()),
        "rules_version": rules.get("rules_version", "unknown"),
        "frameworks": all_results
        }