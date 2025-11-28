from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Set, Any
import json

"""
Lightweight project discovery utilities.

- discover_projects(root) -> dict: find candidate project folders by marker files.
- find_candidate_folders(root) -> List[Path]: return candidate folders (excludes and de-nests).
- classify_folder(folder) -> dict: small metadata for a candidate folder.
- consolidate_discovery(discovery, method) -> dict: aggregate found candidates by top-level or parent.
"""

# candidate marker filenames / globs -> lightweight project-type hints
MARKERS = {
    "node": ["package.json", "yarn.lock"],
    "python": ["pyproject.toml", "requirements.txt", "setup.py"],
    "docker": ["Dockerfile", "docker-compose.yml"],
    "serverless": ["serverless.yml", "serverless.yaml"],
    "angular": ["angular.json"],
    "nest": ["nest-cli.json"],
    "php": ["composer.json"],
    "rust": ["Cargo.toml"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
}

# sensible defaults for excluding noisy folders found inside archives
DEFAULT_EXCLUDES: Set[str] = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "target",
    "__pycache__",
    ".idea",
    ".vscode",
    "site-packages",
    "myenv",
}


def consolidate_discovery(discovery: Dict[str, Any], method: str = "top_level") -> Dict[str, Any]:
    """
    Consolidate discover_projects output.
    method: "top_level" (group by first path part) or "parent" (group by immediate parent)
    Returns summary with aggregated projects list.
    """
    root = Path(discovery.get("scan_root", "."))
    projects = discovery.get("projects", [])

    groups: Dict[str, Dict[str, Any]] = {}
    for p in projects:
        rel = p.get("rel", "")
        parts = rel.split("/") if rel else [rel]
        if method == "parent":
            key = "/".join(parts[:-1]) if len(parts) > 1 else parts[0]
            if key == "":
                key = parts[0]
        else:  # default: top_level
            key = parts[0] if parts and parts[0] else rel

        g = groups.setdefault(key, {"name": key, "members": [], "types": set(), "markers": set()})
        g["members"].append(rel)
        for t in p.get("types", []):
            g["types"].add(t)
        for m in p.get("markers", []):
            g["markers"].add(m)

    # Build result list: convert sets to lists and simple fields
    agg_projects: List[Dict[str, Any]] = []
    for key, g in sorted(groups.items()):
        agg_projects.append({
            "name": key,
            "member_count": len(g["members"]),
            "members": sorted(g["members"]),
            "types": sorted(g["types"]),
            "markers": sorted(g["markers"]),
        })

    summary = {
        "scan_root": discovery.get("scan_root"),
        "original_count": discovery.get("num_projects", 0),
        "aggregated_count": len(agg_projects),
        "projects": agg_projects,
    }
    return summary


def _path_in_excludes(path: Path, excludes: Set[str]) -> bool:
    """
    Return True if any path component matches or contains an exclude token.
    Use substring matching to catch things like 'myenv', 'site-packages', etc.
    """
    parts = [p.lower() for p in path.parts]
    for ex in excludes:
        ex_l = ex.lower()
        for part in parts:
            if part == ex_l or ex_l in part or part.startswith(ex_l):
                return True
    return False


def find_candidate_folders(root: Path, excludes: Set[str] | None = None) -> List[Path]:
    """
    Walk `root` and return folders that look like project roots (contain marker files).
    Filters out excluded paths and nested candidates, keeping only top-level project folders.
    """
    root = root.resolve()
    excludes = set(excludes or DEFAULT_EXCLUDES)
    candidates: Set[Path] = set()

    # quick scan by globs for marker files
    for typ, patterns in MARKERS.items():
        for pat in patterns:
            for p in root.rglob(pat):
                folder = p.parent
                if not _path_in_excludes(folder, excludes):
                    candidates.add(folder)

    # defensive: remove candidates that are under excluded paths
    candidates = {c for c in candidates if not _path_in_excludes(c, excludes)}

    # remove nested candidates: keep only the top-most candidate in a nested tree
    filtered: Set[Path] = set()
    # sort by depth ascending so shallow folders are considered first
    sorted_candidates = sorted(candidates, key=lambda p: len(p.parts))
    for c in sorted_candidates:
        # if any ancestor is already in filtered, skip c
        if any((ancestor in filtered) for ancestor in c.parents):
            continue
        filtered.add(c)

    # ensure deterministic ordering for return
    return sorted(filtered)


def classify_folder(folder: Path) -> Dict[str, object]:
    """
    Return a small classification dict for a candidate folder.
    keys: path, rel, types (list), markers (list)
    """
    types: List[str] = []
    markers: List[str] = []
    for typ, pats in MARKERS.items():
        for pat in pats:
            if (folder / pat).exists():
                if typ not in types:
                    types.append(typ)
                markers.append(pat)
    return {
        "path": str(folder.resolve()),
        "rel": str(folder.relative_to(folder.anchor)) if folder.is_absolute() else str(folder),
        "types": sorted(types),
        "markers": sorted(set(markers)),
    }


# def discover_projects(root: str | Path, excludes: Set[str] | None = None) -> Dict[str, object]:
#     """
#     Discover candidate projects under `root` and return summary structure.
#     """
#     rootp = Path(root).resolve()
#     cand = find_candidate_folders(rootp, excludes)
#     projects = []
#     for f in cand:
#         data = classify_folder(f)
#         # use path relative to scan root for nicer display
#         try:
#             data["rel"] = str(f.relative_to(rootp))
#         except Exception:
#             data["rel"] = str(f)
#         projects.append(data)

#     return {
#         "scan_root": str(rootp),
#         "num_projects": len(projects),
#         "projects": projects,
#     }
# ...existing code...
from .resume_skill_extractor import analyze_project_skills  # add near top imports

def discover_projects(root: str | Path, excludes: Set[str] | None = None, analyze: bool = False) -> Dict[str, object]:
    """
    Discover candidate projects under `root` and optionally run lightweight analysis.
    - analyze: if True, call analyze_project_skills(folder) and attach languages/frameworks/skills.
    """
    rootp = Path(root).resolve()
    cand = find_candidate_folders(rootp, excludes)
    projects = []
    for f in cand:
        data = classify_folder(f)
        # use path relative to scan root for nicer display
        try:
            data["rel"] = str(f.relative_to(rootp))
        except Exception:
            data["rel"] = str(f)

        if analyze:
            try:
                analysis = analyze_project_skills(f)
                # merge safe fields (adjust keys according to your analyzer's return)
                data["languages"] = sorted(analysis.get("languages", []))
                data["frameworks"] = sorted(analysis.get("frameworks", []))
                data["skills"] = sorted(analysis.get("skills", []))
            except Exception as e:
                # don't fail discovery on analyzer error; record reason for debugging
                data.setdefault("analysis_error", str(e))

        projects.append(data)

    return {
        "scan_root": str(rootp),
        "num_projects": len(projects),
        "projects": projects,
    }

def pretty_print_summary(summary: Dict[str, Any]) -> None:
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Project root to scan")
    ap.add_argument("--aggregate", choices=("top_level", "parent"), default=None,
                    help="Aggregate discovered subprojects by top-level or parent")
    args = ap.parse_args()
    result = discover_projects(Path(args.path))
    if args.aggregate:
        result = consolidate_discovery(result, method=args.aggregate)
    pretty_print_summary(result)
