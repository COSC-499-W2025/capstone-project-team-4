import re
import os
import json
from datetime import datetime
from collections import defaultdict

SUPPORTED_LANGUAGES = {
    "javascript", "typescript", "java", "python", "c", "c++", "c#",
    "go", "rust", "php", "ruby", "shell", "powershell", "html",
    "css", "yaml", "json", "markdown", "sql"
}

def get_skill_mapping_path(language):
    base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    base_dir = os.path.abspath(base_dir)
    mapping = os.path.join(base_dir, f"skill_mapping_{language.lower()}.json")
    return mapping if os.path.exists(mapping) else None


def load_mapping(path):
    with open(path, "r", encoding="utf-8") as f:
        return {entry["skill"]: entry["identifiers"] for entry in json.load(f)}

# Fast safe loading
def safe_read_file(path):
    for enc in ["utf-8", "latin-1"]:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except Exception:
            pass
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def pretty_dump(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def analyze_code_file(file_path, language, created_ts=None, modified_ts=None):
    """
    Fast version:
    - Uses re.findall()
    - Returns total matches PER SKILL
    - No line-by-line counting
    - No storing occurrences
    """
    mapping_path = get_skill_mapping_path(language)
    if mapping_path is None:
        return None

    mapping = load_mapping(mapping_path)
    if not os.path.exists(file_path):
        return None

    text = safe_read_file(file_path)
    ts = modified_ts or created_ts

    skill_match_counts = {}

    for skill, patterns in mapping.items():
        total = 0
        for pat in patterns:
            try:
                total += len(re.findall(pat, text))
            except re.error:
                continue

        if total > 0:
            skill_match_counts[skill] = total

    return skill_match_counts, ts


# HEATMAP PURPOSE (SUMMARY)
#
# The heat map tracks *when* each skill is used throughout
# the project timeline. For every match of every skill regex,
# we increment the count for that skill on the file's timestamp
# date. This produces a chronological distribution of skill
# activity, allowing us to visualize:
#
#   - Which skills were used the most
#   - When specific skills were active (by day)
#   - How a developer's skill usage evolved over time

def run_skill_extraction(metadata_path, output_path):
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

    # per match heatmap
    heatmap = defaultdict(lambda: defaultdict(int))

    for f in files:
        lang = f.get("language", "").lower()
        rel = f.get("path")
        created_ts = f.get("created_timestamp")
        modified_ts = f.get("last_modified")

        if lang not in SUPPORTED_LANGUAGES:
            summary["unsupported_languages"][lang] = summary["unsupported_languages"].get(lang, 0) + 1
            summary["files_skipped"] += 1
            continue

        summary["languages_encountered"].add(lang)

        absolute_path = os.path.join(project_root, rel)
        result = analyze_code_file(absolute_path, lang, created_ts, modified_ts)

        if result is None:
            summary["files_skipped"] += 1
            continue

        skill_counts, ts = result

        for skill, count in skill_counts.items():
            # Count matches globally
            summary["global_skill_counts"][skill] += count

            # Heatmap increments PER MATCH
            if ts:
                date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                heatmap[skill][date] += count

        summary["files_analyzed"] += 1

    summary["languages_encountered"] = list(summary["languages_encountered"])

    summary["global_skill_counts"] = dict(
        sorted(summary["global_skill_counts"].items(), key=lambda x: x[1], reverse=True)
    )

    heatmap = {skill: dict(days) for skill, days in heatmap.items()}

    final = {
        "summary": summary,
        "skill_activity_heatmap": heatmap
    }

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pretty_dump(final, output_path)

    return final
