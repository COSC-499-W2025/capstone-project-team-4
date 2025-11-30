import re
import os
import json
from collections import defaultdict

SUPPORTED_LANGUAGES = {
    "javascript", "typescript", "java", "python", "c", "c++", "c#",
    "go", "rust", "php", "ruby", "shell", "powershell", "html",
    "css", "yaml", "json", "markdown", "sql"
}

def get_skill_mapping_path(language):
    base_dir = os.path.join(
        os.path.dirname(__file__),  # src/core/
        "..",                       # src/
        "data"                      # src/data
    )
    base_dir = os.path.abspath(base_dir)

    lang = language.lower()
    mapping = os.path.join(base_dir, f"skill_mapping_{lang}.json")
    return mapping if os.path.exists(mapping) else None

def load_mapping(path):
    """Load mapping file {skill: [regex]}"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {entry["skill"]: entry["identifiers"] for entry in data}

def pretty_dump(data, file_path):
    """Pretty JSON for chronological sorting """
    def serialize(obj, level=0):
        indent = "  " * level

        if not isinstance(obj, (dict, list)):
            return json.dumps(obj)

        if isinstance(obj, list):

            if any(isinstance(x, dict) for x in obj):
                items = [indent + "  " + serialize(x, level + 1) for x in obj]
                return "[\n" + ",\n".join(items) + "\n" + indent + "]"

            if len(obj) <= 12 and all(isinstance(x, (int, float, str)) for x in obj):
                return "[" + ", ".join(json.dumps(x) for x in obj) + "]"

            CHUNK = 15
            lines = []
            for i in range(0, len(obj), CHUNK):
                chunk = obj[i:i+CHUNK]
                chunk_str = ", ".join(json.dumps(x) for x in chunk)
                lines.append(indent + "  " + chunk_str)
            return "[\n" + ",\n".join(lines) + "\n" + indent + "]"

        if isinstance(obj, dict):
            items = []
            for k, v in obj.items():
                key_str = indent + "  " + json.dumps(k) + ": "

                if not isinstance(v, (dict, list)):
                    items.append(key_str + json.dumps(v))
                    continue

                if isinstance(v, list) and len(v) <= 12 and \
                    all(isinstance(x, (int, float, str)) for x in v):
                    items.append(key_str + "[" + ", ".join(json.dumps(x) for x in v) + "]")
                    continue

                items.append(key_str + "\n" + serialize(v, level + 1))

            return "{\n" + ",\n".join(items) + "\n" + indent + "}"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(serialize(data))

def analyze_code_file(file_path, language, loc):
    mapping_path = get_skill_mapping_path(language)
    if mapping_path is None:
        return {"error": f"No mapping for language: {language}"}

    mapping = load_mapping(mapping_path)

    if not os.path.exists(file_path):
        return {"error": f"File missing: {file_path}"}

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    scores = defaultdict(lambda: {
        "raw_count": 0,
        "identifier_summary": defaultdict(int),   # pattern counts
        "occurrence_lines": []                    # line numbers only
    })

    for skill, patterns in mapping.items():
        total = 0
        for pat in patterns:
            try:
                for match in re.finditer(pat, text, flags=re.MULTILINE):
                    total += 1

                    idx = match.start()
                    line = text.count("\n", 0, idx) + 1

                    scores[skill]["identifier_summary"][pat] += 1
                    scores[skill]["occurrence_lines"].append(line)

            except re.error:
                continue

        scores[skill]["raw_count"] = total
        scores[skill]["density_score"] = round((total / max(loc, 1)) * 100, 4)

    # Keep only skills that appear
    non_zero = {
        s: {
            "raw_count": info["raw_count"],
            "identifier_summary": dict(info["identifier_summary"]),
            "occurrence_lines": sorted(info["occurrence_lines"]),
            "density_score": info["density_score"]
        }
        for s, info in scores.items()
        if info["raw_count"] > 0
    }

    return {
        "file_path": file_path,
        "language": language,
        "loc": loc,
        "mapping_used": mapping_path,
        "higher-level skill": non_zero
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
        "global_skill_counts": defaultdict(int),
        "skills_by_language": defaultdict(lambda: defaultdict(int)),
    }

    reports = []
    global_chronology = defaultdict(list)  # skill → list of line numbers

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

        for skill, info in result["higher-level skill"].items():
            count = info["raw_count"]

            summary["global_skill_counts"][skill] += count
            summary["skills_by_language"][lang][skill] += count

            global_chronology[skill].extend(info["occurrence_lines"])

        reports.append(result)
        summary["files_analyzed"] += 1

    summary["languages_encountered"] = list(summary["languages_encountered"])

    summary["global_skill_counts"] = dict(
        sorted(summary["global_skill_counts"].items(), key=lambda x: x[1], reverse=True)
    )

    sorted_lang_skills = {}
    for lang, skill_dict in summary["skills_by_language"].items():
        sorted_lang_skills[lang] = dict(
            sorted(skill_dict.items(), key=lambda x: x[1], reverse=True)
        )
    summary["skills_by_language"] = sorted_lang_skills

    skill_development_order = []
    for skill, lines in global_chronology.items():
        if lines:
            ordered_lines = sorted(lines)
            skill_development_order.append({
                "skill": skill,
                "occurrence_lines": ordered_lines 
            })

    # Sort skills chronologically
    skill_development_order = sorted(
        skill_development_order,
        key=lambda x: x["occurrence_lines"][0] if x["occurrence_lines"] else 99999999
    )

    final = {
        "summary": summary,
        "Chronological Sorting": reports,
        "skill_development_order": skill_development_order
    }

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pretty_dump(final, output_path)

    return final