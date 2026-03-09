"""
Tool and technology detection module.

Detects build tools, CI/CD platforms, containerization, infrastructure,
testing tools, and linting/formatting tools based on YAML rules.

Categories:
- build: Webpack, Vite, Rollup, Make, Maven, Gradle, etc.
- cicd: GitHub Actions, GitLab CI, Jenkins, CircleCI, Travis CI, etc.
- container: Docker, Kubernetes, Helm, etc.
- infrastructure: Terraform, Pulumi, AWS CDK, Ansible, etc.
- testing: Jest, Pytest, JUnit, Cypress, Playwright, etc.
- linting: ESLint, Prettier, Black, Ruff, etc.
- package_manager: npm, Yarn, pnpm, Poetry, etc.
- documentation: Storybook, Swagger, Sphinx, etc.
- deployment: Vercel, Netlify, Heroku, etc.
- monorepo: Lerna, Nx, Turborepo, etc.
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# tomllib: Python 3.11+ / for 3.10 use tomli
try:
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


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


def any_glob(folder: Path, patterns: list[str], excludes: set[str]) -> list[Path]:
    """Find files matching patterns, returns list of matching paths."""
    matches = []
    for pat in patterns:
        for p in folder.rglob(pat):
            if not path_in_excludes(p, excludes):
                matches.append(p)
    return matches


def scan_text_any(folder: Path, needles: list[str], excludes: set[str]) -> bool:
    """Scan text files under folder for any of the needles."""
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
# Rules loading
# =============================================================================

@lru_cache(maxsize=16)
def _load_tool_rules(rules_path: str) -> dict:
    """Load YAML rules from file with caching."""
    raw = Path(rules_path).read_text(encoding="utf-8")
    rules = yaml.safe_load(raw)
    if not isinstance(rules, dict):
        raise ValueError(f"Invalid rules file format: {rules_path}")
    return rules


def get_default_rules_path() -> Path:
    """Get the default path to tools.yml rules file."""
    return Path(__file__).parent.parent / "rules" / "tools.yml"


# =============================================================================
# Signal evaluation (similar to framework.py)
# =============================================================================

def eval_signal(
    sig: dict,
    folder: Path,
    pkg_json: dict | None,
    settings: dict,
) -> tuple[float, list[str], str | None]:
    """
    Evaluate a single signal spec against `folder`.

    Args:
        sig: Signal specification dictionary
        folder: Folder to evaluate
        pkg_json: Parsed package.json if available
        settings: Rules settings

    Returns:
        Tuple of (score_delta, list of emitted signals, config_file that triggered detection)
    """
    t = sig.get("type")
    weight = float(sig.get("weight", 0.0))
    emitted: list[str] = []
    config_file: str | None = None
    excludes = set(settings.get("exclude_dirs", []))

    # --- package.json dependency check ---
    if t == "pkg_json_dep" and pkg_json:
        key = sig.get("key") or "dependencies"
        contains = (sig.get("contains") or "").lower()

        if key in {"dependencies", "devDependencies", "peerDependencies", "optionalDependencies"}:
            deps = pkg_json.get(key) or {}
        else:
            deps = (pkg_json.get("dependencies") or {}) | (pkg_json.get("devDependencies") or {})

        if any(contains in (name or "").lower() for name in deps.keys()):
            emitted.append(f"pkg_json_dep:{key}:{contains}")
            config_file = "package.json"
            return weight, emitted, config_file
        return 0.0, emitted, None

    if t == "pkg_json_script" and pkg_json:
        needle = (sig.get("contains") or "").lower()
        scripts = pkg_json.get("scripts") or {}
        if any(needle in (v or "").lower() for v in scripts.values()):
            emitted.append(f"pkg_json_script:{needle}")
            config_file = "package.json"
            return weight, emitted, config_file
        return 0.0, emitted, None

    # --- file/dir existence ---
    if t == "file_exists":
        p = folder / sig.get("value")
        if p.exists():
            emitted.append(f"file:{sig.get('value')}")
            config_file = sig.get("value")
            return weight, emitted, config_file
        return 0.0, emitted, None

    if t == "file_exists_any":
        for cand in sig.get("value", []):
            if (folder / cand).exists():
                emitted.append(f"file_any:{cand}")
                config_file = cand
                return weight, emitted, config_file
        return 0.0, emitted, None

    if t == "file_exists_glob":
        patterns = sig.get("value") or []
        matches = any_glob(folder, patterns, excludes)
        if matches:
            config_file = str(matches[0].relative_to(folder)) if matches else None
            emitted.append(f"file_glob:{patterns[0] if patterns else '*'}")
            return weight, emitted, config_file
        return 0.0, emitted, None

    if t == "dir_exists":
        p = folder / sig.get("value")
        if p.exists() and p.is_dir():
            emitted.append(f"dir:{sig.get('value')}")
            config_file = sig.get("value")
            return weight, emitted, config_file
        return 0.0, emitted, None

    if t == "dir_exists_any":
        for cand in sig.get("value", []):
            p = folder / cand
            if p.exists() and p.is_dir():
                emitted.append(f"dir_any:{cand}")
                config_file = cand
                return weight, emitted, config_file
        return 0.0, emitted, None

    # --- config file contains text ---
    if t == "cfg_contains":
        needle = sig.get("value") or ""
        if needle and scan_text_any(folder, [needle], excludes):
            emitted.append(f"cfg:{needle}")
            return weight, emitted, None
        return 0.0, emitted, None

    # --- Python: requirements*.txt ---
    if t == "req_txt_contains":
        needle = (sig.get("value") or "").lower()
        candidates = list(folder.glob("requirements*.txt")) + list(folder.rglob("requirements/*.txt"))
        for p in candidates:
            txt = read_text_safe(p) or ""
            if needle in txt.lower():
                emitted.append(f"req:{p.name}:{needle}")
                config_file = p.name
                return weight, emitted, config_file
        return 0.0, emitted, None

    # --- Python: toml_dep (pyproject.toml) ---
    if t in {"toml_dep", "poetry_dep"}:
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

            # Check if key exists (even if empty for tools like black/ruff)
            if cur is not None:
                if not needle:  # Just check if key exists
                    emitted.append(f"toml_key:{key}")
                    config_file = "pyproject.toml"
                    return weight, emitted, config_file

                names: list[str] = []
                if isinstance(cur, dict):
                    names = [k.lower() for k in cur.keys()]
                elif isinstance(cur, list):
                    names = [re.split(r"[<>= ]", x, maxsplit=1)[0].lower() for x in cur]
                if any(needle in n for n in names):
                    emitted.append(f"toml_dep:{key}:{needle}")
                    config_file = "pyproject.toml"
                    return weight, emitted, config_file
        return 0.0, emitted, None

    # --- Maven pom.xml ---
    if t == "pom_contains":
        needle = (sig.get("contains") or "").lower()
        pom = folder / "pom.xml"
        if pom.exists():
            txt = read_text_safe(pom) or ""
            if needle in txt.lower():
                emitted.append(f"pom:{needle}")
                config_file = "pom.xml"
                return weight, emitted, config_file
        return 0.0, emitted, None

    # --- Gradle build.gradle ---
    if t == "gradle_contains":
        needle = (sig.get("contains") or "").lower()
        for gradle_file in ["build.gradle", "build.gradle.kts"]:
            gf = folder / gradle_file
            if gf.exists():
                txt = read_text_safe(gf) or ""
                if needle in txt.lower():
                    emitted.append(f"gradle:{needle}")
                    config_file = gradle_file
                    return weight, emitted, config_file
        return 0.0, emitted, None

    # --- Composer composer.json ---
    if t == "composer_dep":
        needle = (sig.get("contains") or "").lower()
        composer = folder / "composer.json"
        if composer.exists():
            data = load_json_safe(composer)
            if data:
                all_deps = list((data.get("require") or {}).keys()) + list((data.get("require-dev") or {}).keys())
                if any(needle in d.lower() for d in all_deps):
                    emitted.append(f"composer:{needle}")
                    config_file = "composer.json"
                    return weight, emitted, config_file
        return 0.0, emitted, None

    # --- Ruby Gemfile ---
    if t == "gemfile_dep":
        needle = (sig.get("contains") or "").lower()
        gemfile = folder / "Gemfile"
        if gemfile.exists():
            txt = read_text_safe(gemfile) or ""
            if needle in txt.lower():
                emitted.append(f"gemfile:{needle}")
                config_file = "Gemfile"
                return weight, emitted, config_file
        return 0.0, emitted, None

    # --- Go go.mod ---
    if t == "go_mod_dep":
        needle = (sig.get("contains") or "").lower()
        gomod = folder / "go.mod"
        if gomod.exists():
            txt = read_text_safe(gomod) or ""
            if needle in txt.lower():
                emitted.append(f"go_mod:{needle}")
                config_file = "go.mod"
                return weight, emitted, config_file
        return 0.0, emitted, None

    # --- Rust Cargo.toml ---
    if t == "cargo_toml_dep":
        needle = (sig.get("contains") or "").lower()
        cargo = folder / "Cargo.toml"
        if cargo.exists():
            txt = read_text_safe(cargo) or ""
            if needle in txt.lower():
                emitted.append(f"cargo:{needle}")
                config_file = "Cargo.toml"
                return weight, emitted, config_file
        return 0.0, emitted, None

    # --- C# .csproj ---
    if t == "csproj_contains":
        needle = (sig.get("contains") or "").lower()
        for csproj in folder.glob("*.csproj"):
            txt = read_text_safe(csproj) or ""
            if needle in txt.lower():
                emitted.append(f"csproj:{needle}")
                config_file = csproj.name
                return weight, emitted, config_file
        return 0.0, emitted, None

    # Unknown signal type
    return 0.0, emitted, None


# =============================================================================
# Detection pipeline
# =============================================================================

def detect_tools_in_folder(folder: Path, rules: dict) -> list[dict]:
    """
    Detect tools in a single folder using YAML rules.

    Args:
        folder: Folder to analyze
        rules: Parsed YAML rules

    Returns:
        List of detected tool dictionaries
    """
    settings = (rules or {}).get("settings", {}) or {}
    default_min = float(settings.get("default_min_score", 0.5))
    pkg_json = load_json_safe(folder / "package.json")

    results: list[dict] = []

    # Get categories spec
    categories_spec = (rules or {}).get("categories") or {}
    if not isinstance(categories_spec, dict):
        return results

    for category_name, tools_in_category in categories_spec.items():
        if not isinstance(tools_in_category, dict):
            continue

        for tool_name, spec in tools_in_category.items():
            if not isinstance(spec, dict):
                logger.debug("categories.%s.%s is %s; expected dict. Skipped.",
                           category_name, tool_name, type(spec).__name__)
                continue

            score = 0.0
            fired: list[str] = []
            config_file = None

            signals_list = spec.get("signals") or []
            if not isinstance(signals_list, list):
                signals_list = []

            for sig in signals_list:
                if not isinstance(sig, dict):
                    continue
                delta, msgs, cfg = eval_signal(sig, folder, pkg_json, settings)
                if delta:
                    score += delta
                    fired.extend(msgs)
                    if cfg and not config_file:
                        config_file = cfg

            min_needed = float(spec.get("min_score", default_min))
            if score >= min_needed and fired:
                results.append({
                    "name": tool_name,
                    "category": category_name,
                    "confidence": min(1.0, round(score, 3)),
                    "signals": fired[:50],
                    "config_file": config_file,
                })

    return results


def detect_tools_recursive(
    project_root: Path,
    rules_path: str | None = None
) -> dict:
    """
    From the project root, detect tools and technologies.

    Args:
        project_root: Root directory of the project
        rules_path: Path to YAML rules file (default: tools.yml)

    Returns:
        Dictionary with project_root, rules_version, and tools detected
    """
    if rules_path is None:
        rules_path = str(get_default_rules_path())

    rules = _load_tool_rules(rules_path)
    settings = rules.get("settings", {})
    exclude_dirs = set(settings.get("exclude_dirs", []))

    # Detect tools at root level
    all_tools = detect_tools_in_folder(project_root, rules)

    # Also check subdirectories that might be separate projects
    candidates: set[Path] = {project_root}

    # Find subprojects
    for marker in ["package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml"]:
        for f in project_root.rglob(marker):
            if not path_in_excludes(f, exclude_dirs) and f.parent != project_root:
                candidates.add(f.parent)

    # Detect tools in subprojects
    for folder in candidates:
        if folder == project_root:
            continue
        sub_tools = detect_tools_in_folder(folder, rules)
        for tool in sub_tools:
            # Add relative path info
            rel_path = str(folder.relative_to(project_root)).replace("\\", "/")
            tool["location"] = rel_path
            all_tools.append(tool)

    # Deduplicate tools (keep highest confidence)
    seen: dict[str, dict] = {}
    for tool in all_tools:
        key = tool["name"]
        if key not in seen or tool["confidence"] > seen[key]["confidence"]:
            seen[key] = tool

    unique_tools = list(seen.values())

    # Group by category
    by_category: dict[str, list[dict]] = {}
    for tool in unique_tools:
        category = tool["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tool)

    return {
        "project_root": str(project_root.resolve()),
        "rules_version": rules.get("rules_version", "unknown"),
        "tools": unique_tools,
        "by_category": by_category,
        "total_count": len(unique_tools),
    }


# =============================================================================
# Output formatting
# =============================================================================

def pretty_print_results(results: dict) -> None:
    """Print tool detection results in a human-readable format."""
    project_root = results.get("project_root", "(unknown)")
    print(f" Tools detected in: {project_root}\n")

    by_category = results.get("by_category", {})
    if not by_category:
        print("No tools detected.")
        return

    for category, tools in sorted(by_category.items()):
        print(f" {category.upper()}:")
        for tool in tools:
            name = tool.get("name", "(unknown)")
            conf = tool.get("confidence", "?")
            config = tool.get("config_file", "")
            location = tool.get("location", "")
            loc_str = f" [{location}]" if location else ""
            cfg_str = f" ({config})" if config else ""
            print(f"  - {name}{cfg_str}{loc_str} (confidence: {conf})")
        print()
