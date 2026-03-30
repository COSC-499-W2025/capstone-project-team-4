"""
Library detection module.

Extracts dependencies from various package manager files:
- npm (package.json, package-lock.json, yarn.lock)
- pip (requirements.txt, requirements-dev.txt)
- pyproject (pyproject.toml)
- poetry (poetry.lock)
- cargo (Cargo.toml)
- go (go.mod)
- maven (pom.xml)
- gradle (build.gradle, build.gradle.kts)
- gem (Gemfile, Gemfile.lock)
- composer (composer.json, composer.lock)
- nuget (.csproj)
- pub (pubspec.yaml)
"""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
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
# File IO helpers (reuse from framework.py pattern)
# =============================================================================


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


def load_yaml_safe(path: Path) -> dict | None:
    """Load YAML file safely, returning None on error."""
    txt = read_text_safe(path)
    if not txt:
        return None
    try:
        return yaml.safe_load(txt)
    except Exception:
        return None


def path_in_excludes(path: Path, excludes: set[str]) -> bool:
    """Check if any part of the path is in the excludes set."""
    return any(part in excludes for part in path.parts)


# =============================================================================
# Rules loading
# =============================================================================


@lru_cache(maxsize=16)
def _load_library_rules(rules_path: str) -> dict:
    """Load YAML rules from file with caching."""
    raw = Path(rules_path).read_text(encoding="utf-8")
    rules = yaml.safe_load(raw)
    if not isinstance(rules, dict):
        raise ValueError(f"Invalid rules file format: {rules_path}")
    return rules


def get_default_rules_path() -> Path:
    """Get the default path to libraries.yml rules file."""
    return Path(__file__).parent.parent / "rules" / "libraries.yml"


# =============================================================================
# Package parsers
# =============================================================================


def parse_package_json(path: Path) -> list[dict]:
    """
    Parse package.json to extract npm dependencies.

    Returns list of library dicts with name, version, ecosystem, is_dev_dependency.
    """
    data = load_json_safe(path)
    if not data:
        return []

    libraries = []

    # Production dependencies
    for name, version in (data.get("dependencies") or {}).items():
        libraries.append(
            {
                "name": name,
                "version": _clean_version(version),
                "ecosystem": "npm",
                "is_dev_dependency": False,
            }
        )

    # Development dependencies
    for name, version in (data.get("devDependencies") or {}).items():
        libraries.append(
            {
                "name": name,
                "version": _clean_version(version),
                "ecosystem": "npm",
                "is_dev_dependency": True,
            }
        )

    # Peer dependencies (optional, treat as prod)
    for name, version in (data.get("peerDependencies") or {}).items():
        libraries.append(
            {
                "name": name,
                "version": _clean_version(version),
                "ecosystem": "npm",
                "is_dev_dependency": False,
            }
        )

    return libraries


def parse_package_lock(path: Path) -> list[dict]:
    """
    Parse package-lock.json to get all dependencies (direct + transitive).
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        libraries = []

        # NPM 7+ uses packages field
        packages = data.get("packages", {})
        if packages:
            for pkg_path, pkg_data in packages.items():
                if pkg_path == "" or pkg_path == ".":
                    continue
                # Extract package name from path
                parts = pkg_path.split("/")
                if len(parts) >= 2:
                    if parts[1].startswith("@"):
                        pkg_name = (
                            f"{parts[1]}/{parts[2]}" if len(parts) > 2 else parts[1]
                        )
                    else:
                        pkg_name = parts[1]
                    libraries.append(
                        {
                            "name": pkg_name,
                            "version": pkg_data.get("version", ""),
                            "ecosystem": "npm",
                            "is_dev_dependency": pkg_data.get("dev", False),
                        }
                    )

        # Fallback for older format
        if not libraries:
            dependencies = data.get("dependencies", {})
            for name, dep_data in dependencies.items():
                version = (
                    dep_data.get("version", "") if isinstance(dep_data, dict) else ""
                )
                is_dev = (
                    dep_data.get("dev", False) if isinstance(dep_data, dict) else False
                )
                libraries.append(
                    {
                        "name": name,
                        "version": version,
                        "ecosystem": "npm",
                        "is_dev_dependency": is_dev,
                    }
                )

        return libraries
    except Exception as e:
        logger.debug("Could not parse package-lock.json: %s", e)
        return []


def parse_yarn_lock(path: Path) -> list[dict]:
    """Parse yarn.lock to extract dependencies."""
    try:
        content = path.read_text(encoding="utf-8")
        libraries = []
        seen = set()

        # Regex for yarn.lock v1/v2 format
        # Format: "package@version:" or package@version:
        current_pkg = None
        current_version = None

        for line in content.split("\n"):
            line = line.rstrip()

            # Package declaration line
            if not line.startswith(" ") and "@" in line:
                # Extract package name (before @version)
                match = re.match(r'^"?([^@"]+)@', line)
                if match:
                    current_pkg = match.group(1)

            # Version line
            elif line.strip().startswith("version"):
                match = re.search(r'version[:\s]+"?([^"]+)"?', line)
                if match and current_pkg:
                    current_version = match.group(1)
                    if current_pkg not in seen:
                        libraries.append(
                            {
                                "name": current_pkg,
                                "version": current_version,
                                "ecosystem": "npm",
                                "is_dev_dependency": False,  # yarn.lock doesn't distinguish
                            }
                        )
                        seen.add(current_pkg)
                    current_pkg = None
                    current_version = None

        return libraries
    except Exception as e:
        logger.debug("Could not parse yarn.lock: %s", e)
        return []


def parse_requirements_txt(path: Path) -> list[dict]:
    """
    Parse requirements.txt to extract Python dependencies.
    """
    txt = read_text_safe(path)
    if not txt:
        return []

    libraries = []
    is_dev = "dev" in path.name.lower() or "test" in path.name.lower()

    for line in txt.split("\n"):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Skip options like -r, -e, etc.
        if line.startswith("--"):
            continue

        # Parse package name and version
        # Formats: package, package==1.0, package>=1.0, package[extra]==1.0
        match = re.match(r"^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)\s*([<>=!~]+.+)?", line)
        if match:
            name = match.group(1).split("[")[0]  # Remove extras
            version = _clean_version(match.group(2)) if match.group(2) else ""
            libraries.append(
                {
                    "name": name,
                    "version": version,
                    "ecosystem": "pip",
                    "is_dev_dependency": is_dev,
                }
            )

    return libraries


def parse_pyproject_toml(path: Path) -> list[dict]:
    """
    Parse pyproject.toml to extract Python dependencies.

    Supports both PEP 621 (project.dependencies) and Poetry (tool.poetry.dependencies).
    """
    data = load_toml_safe(path)
    if not data:
        return []

    libraries = []

    # PEP 621 format: project.dependencies
    project_deps = data.get("project", {}).get("dependencies", [])
    if isinstance(project_deps, list):
        for dep in project_deps:
            name, version = _parse_pep508_dependency(dep)
            if name:
                libraries.append(
                    {
                        "name": name,
                        "version": version,
                        "ecosystem": "pyproject",
                        "is_dev_dependency": False,
                    }
                )

    # PEP 621: optional-dependencies (often dev deps)
    optional_deps = data.get("project", {}).get("optional-dependencies", {})
    for group, deps in optional_deps.items():
        is_dev = group.lower() in {"dev", "development", "test", "testing", "docs"}
        if isinstance(deps, list):
            for dep in deps:
                name, version = _parse_pep508_dependency(dep)
                if name:
                    libraries.append(
                        {
                            "name": name,
                            "version": version,
                            "ecosystem": "pyproject",
                            "is_dev_dependency": is_dev,
                        }
                    )

    # Poetry format: tool.poetry.dependencies
    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    if isinstance(poetry_deps, dict):
        for name, spec in poetry_deps.items():
            if name.lower() == "python":
                continue
            version = ""
            if isinstance(spec, str):
                version = _clean_version(spec)
            elif isinstance(spec, dict):
                version = _clean_version(spec.get("version", ""))
            libraries.append(
                {
                    "name": name,
                    "version": version,
                    "ecosystem": "poetry",
                    "is_dev_dependency": False,
                }
            )

    # Poetry: dev-dependencies (older format)
    poetry_dev = data.get("tool", {}).get("poetry", {}).get("dev-dependencies", {})
    if isinstance(poetry_dev, dict):
        for name, spec in poetry_dev.items():
            version = ""
            if isinstance(spec, str):
                version = _clean_version(spec)
            elif isinstance(spec, dict):
                version = _clean_version(spec.get("version", ""))
            libraries.append(
                {
                    "name": name,
                    "version": version,
                    "ecosystem": "poetry",
                    "is_dev_dependency": True,
                }
            )

    # Poetry: group dependencies (newer format)
    poetry_groups = data.get("tool", {}).get("poetry", {}).get("group", {})
    for group_name, group_data in poetry_groups.items():
        is_dev = group_name.lower() in {"dev", "development", "test", "testing", "docs"}
        group_deps = (
            group_data.get("dependencies", {}) if isinstance(group_data, dict) else {}
        )
        for name, spec in group_deps.items():
            version = ""
            if isinstance(spec, str):
                version = _clean_version(spec)
            elif isinstance(spec, dict):
                version = _clean_version(spec.get("version", ""))
            libraries.append(
                {
                    "name": name,
                    "version": version,
                    "ecosystem": "poetry",
                    "is_dev_dependency": is_dev,
                }
            )

    return libraries


def parse_poetry_lock(path: Path) -> list[dict]:
    """Parse poetry.lock to extract Python dependencies."""
    try:
        content = path.read_text(encoding="utf-8")
        libraries = []

        current_name = ""
        current_version = ""

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("[[package]]"):
                if current_name:
                    libraries.append(
                        {
                            "name": current_name,
                            "version": current_version,
                            "ecosystem": "poetry",
                            "is_dev_dependency": False,
                        }
                    )
                current_name = ""
                current_version = ""
            elif line.startswith("name ="):
                match = re.search(r'name = "([^"]+)"', line)
                if match:
                    current_name = match.group(1)
            elif line.startswith("version ="):
                match = re.search(r'version = "([^"]+)"', line)
                if match:
                    current_version = match.group(1)

        # Don't forget the last package
        if current_name:
            libraries.append(
                {
                    "name": current_name,
                    "version": current_version,
                    "ecosystem": "poetry",
                    "is_dev_dependency": False,
                }
            )

        return libraries
    except Exception as e:
        logger.debug("Could not parse poetry.lock: %s", e)
        return []


def parse_cargo_toml(path: Path) -> list[dict]:
    """Parse Cargo.toml to extract Rust dependencies."""
    data = load_toml_safe(path)
    if not data:
        return []

    libraries = []

    # Regular dependencies
    for name, spec in (data.get("dependencies") or {}).items():
        version = ""
        if isinstance(spec, str):
            version = spec
        elif isinstance(spec, dict):
            version = spec.get("version", "")
        libraries.append(
            {
                "name": name,
                "version": version,
                "ecosystem": "cargo",
                "is_dev_dependency": False,
            }
        )

    # Dev dependencies
    for name, spec in (data.get("dev-dependencies") or {}).items():
        version = ""
        if isinstance(spec, str):
            version = spec
        elif isinstance(spec, dict):
            version = spec.get("version", "")
        libraries.append(
            {
                "name": name,
                "version": version,
                "ecosystem": "cargo",
                "is_dev_dependency": True,
            }
        )

    # Build dependencies
    for name, spec in (data.get("build-dependencies") or {}).items():
        version = ""
        if isinstance(spec, str):
            version = spec
        elif isinstance(spec, dict):
            version = spec.get("version", "")
        libraries.append(
            {
                "name": name,
                "version": version,
                "ecosystem": "cargo",
                "is_dev_dependency": False,
            }
        )

    return libraries


def parse_go_mod(path: Path) -> list[dict]:
    """Parse go.mod to extract Go dependencies."""
    txt = read_text_safe(path)
    if not txt:
        return []

    libraries = []
    in_require = False

    for line in txt.split("\n"):
        line = line.strip()

        # Handle require block
        if line.startswith("require ("):
            in_require = True
            continue
        elif line == ")":
            in_require = False
            continue

        # Handle single-line require
        if line.startswith("require "):
            match = re.match(r"require\s+(\S+)\s+(\S+)", line)
            if match:
                libraries.append(
                    {
                        "name": match.group(1),
                        "version": match.group(2).lstrip("v"),
                        "ecosystem": "go",
                        "is_dev_dependency": False,
                    }
                )
            continue

        # Inside require block
        if in_require and line and not line.startswith("//"):
            parts = line.split()
            if len(parts) >= 2:
                libraries.append(
                    {
                        "name": parts[0],
                        "version": parts[1].lstrip("v"),
                        "ecosystem": "go",
                        "is_dev_dependency": False,
                    }
                )

    return libraries


def parse_pom_xml(path: Path) -> list[dict]:
    """Parse pom.xml to extract Maven dependencies."""
    txt = read_text_safe(path)
    if not txt:
        return []

    libraries = []

    try:
        # Remove namespace for easier parsing
        txt = re.sub(r'\sxmlns="[^"]+"', "", txt, count=1)
        root = ET.fromstring(txt)

        # Find all dependency elements
        for dep in root.findall(".//dependency"):
            group_id = dep.find("groupId")
            artifact_id = dep.find("artifactId")
            version = dep.find("version")
            scope = dep.find("scope")

            if artifact_id is not None:
                name = (
                    f"{group_id.text}:{artifact_id.text}"
                    if group_id is not None
                    else artifact_id.text
                )
                libraries.append(
                    {
                        "name": name,
                        "version": version.text if version is not None else "",
                        "ecosystem": "maven",
                        "is_dev_dependency": scope is not None
                        and scope.text in {"test", "provided"},
                    }
                )
    except Exception as e:
        logger.debug("Could not parse pom.xml: %s", e)

    return libraries


def parse_build_gradle(path: Path) -> list[dict]:
    """Parse build.gradle or build.gradle.kts to extract Gradle dependencies."""
    txt = read_text_safe(path)
    if not txt:
        return []

    libraries = []

    # Match various dependency formats
    # implementation 'group:artifact:version'
    # testImplementation("group:artifact:version")
    patterns = [
        r"(?:implementation|api|compileOnly|runtimeOnly|testImplementation|testCompileOnly|testRuntimeOnly)\s*['\"]([^'\"]+)['\"]",
        r"(?:implementation|api|compileOnly|runtimeOnly|testImplementation|testCompileOnly|testRuntimeOnly)\s*\(['\"]([^'\"]+)['\"]\)",
    ]

    dev_keywords = {"testImplementation", "testCompileOnly", "testRuntimeOnly"}

    for pattern in patterns:
        for match in re.finditer(pattern, txt):
            dep = match.group(1)
            parts = dep.split(":")

            # Check if it's a test dependency
            full_match = match.group(0)
            is_dev = any(kw in full_match for kw in dev_keywords)

            if len(parts) >= 2:
                libraries.append(
                    {
                        "name": f"{parts[0]}:{parts[1]}",
                        "version": parts[2] if len(parts) > 2 else "",
                        "ecosystem": "gradle",
                        "is_dev_dependency": is_dev,
                    }
                )

    return libraries


def parse_gemfile(path: Path) -> list[dict]:
    """Parse Gemfile to extract Ruby dependencies."""
    txt = read_text_safe(path)
    if not txt:
        return []

    libraries = []
    in_dev_group = False

    for line in txt.split("\n"):
        line = line.strip()

        # Track group context
        if "group :development" in line or "group :test" in line:
            in_dev_group = True
        elif line == "end":
            in_dev_group = False

        # Match gem declarations
        match = re.match(r"gem\s+['\"]([^'\"]+)['\"](?:,\s*['\"]([^'\"]+)['\"])?", line)
        if match:
            libraries.append(
                {
                    "name": match.group(1),
                    "version": _clean_version(match.group(2)) if match.group(2) else "",
                    "ecosystem": "gem",
                    "is_dev_dependency": in_dev_group,
                }
            )

    return libraries


def parse_gemfile_lock(path: Path) -> list[dict]:
    """Parse Gemfile.lock to extract Ruby dependencies."""
    txt = read_text_safe(path)
    if not txt:
        return []

    libraries = []
    in_specs = False

    for line in txt.split("\n"):
        if line.strip() == "specs:":
            in_specs = True
            continue
        elif line and not line.startswith(" "):
            in_specs = False
            continue

        if in_specs:
            # Match gem name and version: "    gem_name (1.2.3)"
            match = re.match(r"^\s{4}(\S+)\s+\(([^)]+)\)", line)
            if match:
                libraries.append(
                    {
                        "name": match.group(1),
                        "version": match.group(2),
                        "ecosystem": "gem",
                        "is_dev_dependency": False,
                    }
                )

    return libraries


def parse_composer_json(path: Path) -> list[dict]:
    """Parse composer.json to extract PHP dependencies."""
    data = load_json_safe(path)
    if not data:
        return []

    libraries = []

    # Regular dependencies
    for name, version in (data.get("require") or {}).items():
        if name.lower() in {"php", "ext-*"} or name.startswith("ext-"):
            continue
        libraries.append(
            {
                "name": name,
                "version": _clean_version(version),
                "ecosystem": "composer",
                "is_dev_dependency": False,
            }
        )

    # Dev dependencies
    for name, version in (data.get("require-dev") or {}).items():
        libraries.append(
            {
                "name": name,
                "version": _clean_version(version),
                "ecosystem": "composer",
                "is_dev_dependency": True,
            }
        )

    return libraries


def parse_csproj(path: Path) -> list[dict]:
    """Parse .csproj to extract NuGet dependencies."""
    txt = read_text_safe(path)
    if not txt:
        return []

    libraries = []

    try:
        root = ET.fromstring(txt)

        for ref in root.findall(".//PackageReference"):
            name = ref.get("Include")
            version = ref.get("Version", "")
            if name:
                libraries.append(
                    {
                        "name": name,
                        "version": version,
                        "ecosystem": "nuget",
                        "is_dev_dependency": False,
                    }
                )
    except Exception as e:
        logger.debug("Could not parse .csproj: %s", e)

    return libraries


def parse_pubspec_yaml(path: Path) -> list[dict]:
    """Parse pubspec.yaml to extract Dart/Flutter dependencies."""
    data = load_yaml_safe(path)
    if not data:
        return []

    libraries = []

    # Regular dependencies
    for name, spec in (data.get("dependencies") or {}).items():
        if name.lower() == "flutter":
            continue
        version = ""
        if isinstance(spec, str):
            version = spec
        elif isinstance(spec, dict):
            version = spec.get("version", "")
        libraries.append(
            {
                "name": name,
                "version": _clean_version(version) if version else "",
                "ecosystem": "pub",
                "is_dev_dependency": False,
            }
        )

    # Dev dependencies
    for name, spec in (data.get("dev_dependencies") or {}).items():
        version = ""
        if isinstance(spec, str):
            version = spec
        elif isinstance(spec, dict):
            version = spec.get("version", "")
        libraries.append(
            {
                "name": name,
                "version": _clean_version(version) if version else "",
                "ecosystem": "pub",
                "is_dev_dependency": True,
            }
        )

    return libraries


# =============================================================================
# Helper functions
# =============================================================================


def _clean_version(version: str | None) -> str:
    """Clean version string by removing operators."""
    if not version:
        return ""
    # Remove common version operators
    version = re.sub(r"^[~^>=<!\s]+", "", str(version))
    return version.strip()


def _parse_pep508_dependency(dep: str) -> tuple[str, str]:
    """Parse PEP 508 dependency string (e.g., 'package>=1.0')."""
    if not dep:
        return "", ""

    # Remove extras and environment markers
    dep = dep.split(";")[0].strip()

    # Extract name and version
    match = re.match(r"^([a-zA-Z0-9_-]+)(?:\[.*?\])?\s*([<>=!~].*)?$", dep)
    if match:
        name = match.group(1)
        version = _clean_version(match.group(2)) if match.group(2) else ""
        return name, version

    return dep.split("[")[0], ""


# =============================================================================
# Main detection function
# =============================================================================


def detect_libraries_recursive(
    project_root: Path, rules_path: str | None = None
) -> dict:
    """
    Recursively scan project and extract all libraries from package manager files.

    Args:
        project_root: Root directory of the project
        rules_path: Path to YAML rules file (default: libraries.yml)

    Returns:
        Dictionary with project_root, rules_version, and libraries by ecosystem
    """
    if rules_path is None:
        rules_path = str(get_default_rules_path())

    rules = _load_library_rules(rules_path)
    settings = rules.get("settings", {})
    exclude_dirs = set(settings.get("exclude_dirs", []))

    all_libraries: list[dict] = []
    processed_files: set[str] = set()

    # Define parsers for each file type
    file_parsers = {
        "package.json": parse_package_json,
        "package-lock.json": parse_package_lock,
        "yarn.lock": parse_yarn_lock,
        "requirements.txt": parse_requirements_txt,
        "requirements-dev.txt": parse_requirements_txt,
        "requirements-test.txt": parse_requirements_txt,
        "pyproject.toml": parse_pyproject_toml,
        "poetry.lock": parse_poetry_lock,
        "Cargo.toml": parse_cargo_toml,
        "go.mod": parse_go_mod,
        "pom.xml": parse_pom_xml,
        "build.gradle": parse_build_gradle,
        "build.gradle.kts": parse_build_gradle,
        "Gemfile": parse_gemfile,
        "Gemfile.lock": parse_gemfile_lock,
        "composer.json": parse_composer_json,
        "pubspec.yaml": parse_pubspec_yaml,
    }

    # Scan for package manager files
    for filename, parser in file_parsers.items():
        for file_path in project_root.rglob(filename):
            if path_in_excludes(file_path, exclude_dirs):
                continue

            file_key = str(file_path.resolve())
            if file_key in processed_files:
                continue
            processed_files.add(file_key)

            try:
                libraries = parser(file_path)
                all_libraries.extend(libraries)
            except Exception as e:
                logger.debug("Failed to parse %s: %s", file_path, e)

    # Scan for requirements*.txt files
    for req_file in project_root.rglob("requirements*.txt"):
        if path_in_excludes(req_file, exclude_dirs):
            continue
        file_key = str(req_file.resolve())
        if file_key in processed_files:
            continue
        processed_files.add(file_key)

        try:
            libraries = parse_requirements_txt(req_file)
            all_libraries.extend(libraries)
        except Exception as e:
            logger.debug("Failed to parse %s: %s", req_file, e)

    # Scan for .csproj files
    for csproj_file in project_root.rglob("*.csproj"):
        if path_in_excludes(csproj_file, exclude_dirs):
            continue
        file_key = str(csproj_file.resolve())
        if file_key in processed_files:
            continue
        processed_files.add(file_key)

        try:
            libraries = parse_csproj(csproj_file)
            all_libraries.extend(libraries)
        except Exception as e:
            logger.debug("Failed to parse %s: %s", csproj_file, e)

    # Deduplicate libraries (keep first occurrence)
    seen = set()
    unique_libraries = []
    for lib in all_libraries:
        key = (lib["name"].lower(), lib["ecosystem"])
        if key not in seen:
            seen.add(key)
            unique_libraries.append(lib)

    # Group by ecosystem for summary
    by_ecosystem: dict[str, list[dict]] = {}
    for lib in unique_libraries:
        ecosystem = lib["ecosystem"]
        if ecosystem not in by_ecosystem:
            by_ecosystem[ecosystem] = []
        by_ecosystem[ecosystem].append(lib)

    return {
        "project_root": str(project_root.resolve()),
        "rules_version": rules.get("rules_version", "unknown"),
        "libraries": unique_libraries,
        "by_ecosystem": by_ecosystem,
        "total_count": len(unique_libraries),
    }
