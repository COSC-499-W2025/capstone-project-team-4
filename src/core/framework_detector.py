from __future__ import annotations
from pathlib import Path
from fnmatch import fnmatch
import argparse
import json
import re
import sys
import yaml

"""
- Recursively scans a project and detects frameworks based on YAML rules (frameworks.yml)
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
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

def read_bytes_safe(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except Exception:
        return None

def load_json_safe(path: Path) -> dict | None:
    txt = read_text_safe(path)
    if not txt:
        return None
    try:
        return json.loads(txt)
    except Exception:
        return None

def load_toml_safe(path: Path) -> dict | None:
    raw = read_bytes_safe(path)
    if not raw:
        return None
    try:
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


# =============================
# Signal evaluation
# =============================

def eval_signal(sig: dict, folder: Path, pkg_json: dict | None, settings: dict) -> tuple[float, list[str]]:
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

    # --- generic text contains / import snippets ---
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
                names = [re.split(r"[<>= ]", x, 1)[0].lower() for x in cur]
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
    Detect frameworks in a single folder using YAML rules.
    Reads package.json if present (for pkg_json_* signals),
    and evaluates all supported signals against files under the folder.
    """
    settings = (rules or {}).get("settings", {}) or {}
    default_min = float(settings.get("default_min_score", 0.7))
    pkg_json = load_json_safe(folder / "package.json")

    results: list[dict] = []

    # Prevent crashes if the 'frameworks' section is missing or invalid
    frameworks_spec = (rules or {}).get("frameworks") or {}
    if not isinstance(frameworks_spec, dict):
        frameworks_spec = {}

    for fw_name, spec in frameworks_spec.items():
        # ★ This was the previous crash point — skip if the spec is not a dictionary (e.g., None, string, etc.)
        if not isinstance(spec, dict):
            # Optional: print a warning if needed
            # print(f"[WARN] frameworks.{fw_name} is {type(spec).__name__}; expected dict. Skipped.")
            continue

        score = 0.0
        fired: list[str] = []

        signals_list = spec.get("signals") or []
        if not isinstance(signals_list, list):
            # Optional: print a warning if the 'signals' field is malformed
            # print(f"[WARN] frameworks.{fw_name}.signals is not a list. Skipped.")
            signals_list = []

        for sig in signals_list:
            if not isinstance(sig, dict):
                continue
            delta, msgs = eval_signal(sig, folder, pkg_json, settings)
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
    raw = Path(rules_path).read_text(encoding="utf-8")
    rules = yaml.safe_load(raw) 
    if not isinstance(rules, dict):
        raise ValueError(f"Invalid rules file format: {rules_path}")
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
        relative = str(folder.relative_to(project_root)) if folder != project_root else "."
        fw_list = detect_frameworks_in_folder(folder, rules)
        if fw_list:
            all_results[relative] = fw_list

    return {
        "project_root": str(project_root.resolve()),
        "rules_version": rules.get("rules_version", "unknown"),
        "frameworks": all_results
    }


# =============================
# Output
# =============================

def pretty_print_results(results):
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


# =============================
# CLI
# =============================

def main():
    parser = argparse.ArgumentParser(description="Detect frameworks recursively in monorepo projects")
    parser.add_argument("path", help="Path to project root")
    parser.add_argument("--rules", default="src/core/rules/frameworks.yml", help="Path to YAML rules file")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    results = detect_frameworks_recursive(root, args.rules)
    pretty_print_results(results)

if __name__ == "__main__":
    main()
