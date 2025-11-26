import re
import os
import json
from collections import defaultdict

# ------------------------------------------------------
# Supported languages
# ------------------------------------------------------
SUPPORTED_LANGUAGES = {
    "javascript","typescript","java","python","c","c++","c#",
    "go","rust","php","ruby","shell","powershell","html",
    "css","yaml","json","markdown","sql" }

# ------------------------------------------------------
# 1. select mapping based on language
# ------------------------------------------------------
def get_skill_mapping_path(language):
    base_dir = "/Users/kusshsatija/capstone-project-team-4/src/data"
    lang = language.lower()
    mapping_file = os.path.join(base_dir, f"skill_mapping_{lang}.json")
    
    if not os.path.exists(mapping_file):
        print(f"⚠️  Warning: No skill mapping found for language '{language}' at {mapping_file}")
        return None

    return mapping_file


# ------------------------------------------------------
# 2. Load mapping JSON
# ------------------------------------------------------
def load_skill_mapping(skill_mapping_path):
    try:
        with open(skill_mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {entry["skill"]: entry["identifiers"] for entry in data}
    except Exception as e:
        print(f"❌ Error loading skill mapping: {e}")
        return None


# ------------------------------------------------------
# 3. Analyze single file
# ------------------------------------------------------
def analyze_code_file(file_path, detected_language, loc):
    if loc is None or loc < 0:
        loc = 1  # placeholder to avoid division errors

    skill_mapping_path = get_skill_mapping_path(detected_language)
    if skill_mapping_path is None:
        return {"error": f"No mapping for language: {detected_language}"}

    skill_mapping = load_skill_mapping(skill_mapping_path)
    if skill_mapping is None:
        return {"error": "Skill mapping failed to load."}

    if not os.path.exists(file_path):
        return {"error": f"Code file not found: {file_path}"}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        return {"error": f"Could not read file: {e}"}

    skill_scores = defaultdict(lambda: {"raw_count": 0, "identifier_list": []})

    for skill, patterns in skill_mapping.items():
        total_matches = 0

        for pattern in patterns:
            try:
                matches = re.findall(pattern, code_content, flags=re.MULTILINE)
                if matches:
                    skill_scores[skill]["identifier_list"].append(
                        f"{pattern} ({len(matches)})"
                    )
                total_matches += len(matches)
            except re.error as e:
                print(f"⚠️ Regex error ({pattern}): {e}")

        skill_scores[skill]["raw_count"] = total_matches
        skill_scores[skill]["density_score"] = round((total_matches / loc) * 100, 4)

    # ---------------------------------------------------------
    # NEW: Filter out zero-count skills
    # ---------------------------------------------------------
    non_zero_skills = {
        skill: data
        for skill, data in skill_scores.items()
        if data["raw_count"] > 0
    }

    return {
        "file_path": file_path,
        "language": detected_language,
        "mapping_used": skill_mapping_path,
        "loc": loc,
        "skill_scores": non_zero_skills   # <<< updated
    }


# ------------------------------------------------------
# 4. MAIN: read metadata and process multiple files
# ------------------------------------------------------
def main():

    metadata_path = "/Users/kusshsatija/capstone-project-team-4/src/outputs/app_metadata.json"

    if not os.path.exists(metadata_path):
        print("❌ app_metadata.json not found.")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    files = metadata.get("files", [])
    results = []

    summary = {
        "total_files_in_metadata": len(files),
        "files_analyzed": 0,
        "files_skipped": 0,
        "languages_encountered": set(),
        "reports_generated": 0,
        "unsupported_languages": {},
        "global_skill_counts": defaultdict(int)
    }

    print("\n🔍 Starting skill extraction for metadata files...\n")

    for entry in files:
        lang = entry.get("language", "").lower()
        file_path = entry.get("path")

        if not lang or not file_path:
            summary["files_skipped"] += 1
            continue

        if lang not in SUPPORTED_LANGUAGES:
            summary["unsupported_languages"].setdefault(lang, 0)
            summary["unsupported_languages"][lang] += 1
            summary["files_skipped"] += 1
            continue

        absolute_path = file_path.replace(
            "/app", "/Users/kusshsatija/capstone-project-team-4"
        )
        summary["languages_encountered"].add(lang)

        loc = 1  # placeholder

        result = analyze_code_file(absolute_path, lang, loc)

        if "error" in result:
            summary["files_skipped"] += 1
            continue

        # Aggregate skill counts (only non-zero inside result)
        for skill, info in result["skill_scores"].items():
            summary["global_skill_counts"][skill] += info["raw_count"]

        results.append(result)
        summary["files_analyzed"] += 1
        summary["reports_generated"] += 1

    summary["languages_encountered"] = list(summary["languages_encountered"])

    summary["global_skill_counts"] = dict(
        sorted(summary["global_skill_counts"].items(), key=lambda x: x[1], reverse=True)
    )

    output_path = "/Users/kusshsatija/capstone-project-team-4/src/outputs/alternate_skill_extraction_output.json"

    final_output = {
        "summary": summary,
        "file_reports": results
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)

    print(f"\n💾 Skill extraction complete! Saved to:\n{output_path}\n")


if __name__ == "__main__":
    main()
