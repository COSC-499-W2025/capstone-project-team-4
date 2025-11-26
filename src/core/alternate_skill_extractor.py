import re
import os
import json
from collections import defaultdict

SUPPORTED_LANGUAGES = {
    "javascript","typescript","java","python","c","c++","c#",
    "go","rust","php","ruby","shell","powershell","html",
    "css","yaml","json","markdown","sql"
}

def get_skill_mapping_path(language):
    base_dir = "/Users/kusshsatija/capstone-project-team-4/src/data"
    lang = language.lower()
    mapping = os.path.join(base_dir, f"skill_mapping_{lang}.json")
    return mapping if os.path.exists(mapping) else None


def load_mapping(path):
    """Load mapping file {skill: [regex]}"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {entry["skill"]: entry["identifiers"] for entry in data}


def analyze_code_file(file_path, language, loc):
    """Analyze a single file and return skill matches."""
    mapping_path = get_skill_mapping_path(language)
    if mapping_path is None:
        return {"error": f"No mapping for language: {language}"}

    mapping = load_mapping(mapping_path)

    if not os.path.exists(file_path):
        return {"error": f"File missing: {file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    scores = defaultdict(lambda: {"raw_count": 0, "identifier_list": []})

    for skill, patterns in mapping.items():
        total = 0
        for pat in patterns:
            try:
                matches = re.findall(pat, text, flags=re.MULTILINE)
                if matches:
                    scores[skill]["identifier_list"].append(f"{pat} ({len(matches)})")
                total += len(matches)
            except re.error:
                continue

        scores[skill]["raw_count"] = total
        scores[skill]["density_score"] = round((total / max(loc, 1)) * 100, 4)

    # Only return non-zero skills
    non_zero = {s: info for s, info in scores.items() if info["raw_count"] > 0}

    return {
        "file_path": file_path,
        "language": language,
        "loc": loc,
        "mapping_used": mapping_path,
        "skill_scores": non_zero
    }


def run_skill_extraction(metadata_path, output_path):
    if not os.path.exists(metadata_path):
        return {"error": f"Metadata not found: {metadata_path}"}

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    project_root = meta["project_root"]
    files = meta["files"]

    summary = {
        "total_files": len(files),
        "files_analyzed": 0,
        "files_skipped": 0,
        "languages_encountered": set(),
        "unsupported_languages": {},
        "global_skill_counts": defaultdict(int)
    }

    reports = []

    for f in files:
        lang = f.get("language", "").lower()
        loc = f.get("lines_of_code", 0)
        rel = f.get("path")

        if lang not in SUPPORTED_LANGUAGES:
            summary["unsupported_languages"].setdefault(lang, 0)
            summary["unsupported_languages"][lang] += 1
            summary["files_skipped"] += 1
            continue

        absolute_path = os.path.join(project_root, rel)
        summary["languages_encountered"].add(lang)

        result = analyze_code_file(absolute_path, lang, loc)
        if "error" in result:
            summary["files_skipped"] += 1
            continue

        # aggregate global skills
        for skill, info in result["skill_scores"].items():
            summary["global_skill_counts"][skill] += info["raw_count"]

        reports.append(result)
        summary["files_analyzed"] += 1

    summary["languages_encountered"] = list(summary["languages_encountered"])
    summary["global_skill_counts"] = dict(
        sorted(summary["global_skill_counts"].items(), key=lambda x: x[1], reverse=True)
    )

    final = {
        "summary": summary,
        "file_reports": reports
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=4)

    return {"success": True, "output": output_path}
