import re
import os
import json
from collections import defaultdict

# NEED TO CHANGE ONCE IN DEVELOPMENT TO IMPORT FILE PATH AND LANGUAGE DETECTED

# ---------------------------------------------
# 1. select mapping based on language
# ---------------------------------------------
def get_skill_mapping_path(language):
    """
    Build mapping path like:
    /Users/kusshsatija/capstone-project-team-4/src/data/skill_mapping_<language>.json
    """

    base_dir = "/Users/kusshsatija/capstone-project-team-4/src/data"
    lang = language.lower()
    mapping_file = os.path.join(base_dir, f"skill_mapping_{lang}.json")
    
    if not os.path.exists(mapping_file):
        print(f"Warning: Mapping file not found for language '{language}' at {mapping_file}")
        return None

    return mapping_file


# ---------------------------------------------
# 2. Load mapping JSON
# ---------------------------------------------
def load_skill_mapping(skill_mapping_path):
    try:
        if not os.path.exists(skill_mapping_path):
            print(f"Error: Skill mapping file not found at {skill_mapping_path}")
            return None

        with open(skill_mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {entry["skill"]: entry["identifiers"] for entry in data}

    except Exception as e:
        print(f"Error loading skill mapping: {e}")
        return None


# ---------------------------------------------
# 3. Analyze code with mapping
# ---------------------------------------------
def analyze_code_file(file_path, detected_language, loc):
    if loc is None or loc < 0:
        return {"error": "LOC (lines of code) must be provided and non-negative."}

    skill_mapping_path = get_skill_mapping_path(detected_language)
    if skill_mapping_path is None:
        return {"error": f"No mapping found for language: {detected_language}"}

    skill_mapping = load_skill_mapping(skill_mapping_path)
    if skill_mapping is None:
        return {"error": "Failed to load skill mapping file."}

    if not os.path.exists(file_path):
        return {"error": f"Code file not found: {file_path}"}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        return {"error": f"Error reading code file: {e}"}

    skill_scores = defaultdict(lambda: {"raw_count": 0, "identifier_list": []})

    for skill, patterns in skill_mapping.items():
        count = 0

        for pattern in patterns:
            try:
                matches = re.findall(pattern, code_content, flags=re.MULTILINE)
                match_count = len(matches)
            except re.error as e:
                print(f"Regex error: Skill '{skill}', Pattern '{pattern}' → {e}")
                continue

            if match_count > 0:
                skill_scores[skill]["identifier_list"].append(
                    f"{pattern} ({match_count})"
                )
                count += match_count

        skill_scores[skill]["raw_count"] = count
        skill_scores[skill]["density_score"] = (
            round(count / loc * 100, 4) if loc > 0 else 0
        )

    return {
        "language": detected_language,
        "skill_mapping_used": skill_mapping_path,
        "total_lines_of_code": loc,
        "skill_scores": dict(skill_scores)
    }


# --------------------------------------------------
# 4. MANUAL TEST CONFIGURATION + SAVE TO JSON
# --------------------------------------------------
def main():

    # >>>>> CHANGE THESE VALUES TO TEST <<<<<
    file_path = "/Users/kusshsatija/capstone-project-team-4/src/core/framework_detector.py"
    detected_language = "python"
    loc = 429

    print("\nRunning manual skill extraction test...\n")

    result = analyze_code_file(file_path, detected_language, loc)

    if "error" in result:
        print("❌ Error:", result["error"])
        return

    # -----------------------------
    # Save results to a JSON file
    # -----------------------------
    output_path = "/Users/kusshsatija/capstone-project-team-4/src/outputs/alternate_skill_extraction_output.json"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)
        print(f"\n💾 Results saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving JSON file: {e}")

    # -----------------------------
    # Terminal display
    # -----------------------------
    print("\n=====================================")
    print("        SKILL EXTRACTION RESULTS     ")
    print("=====================================")

    print(f"📌 Language: {result['language']}")
    print(f"📄 Mapping File: {result['skill_mapping_used']}")
    print(f"📏 Total LOC: {result['total_lines_of_code']}")

    print("\n🧠 Identified Skills:")
    for skill, info in result["skill_scores"].items():
        if info["raw_count"] > 0:
            print(f"\n🔹 {skill}")
            print(f"   Count: {info['raw_count']}")
            print(f"   Density: {info['density_score']}%")
            print(f"   Matches:")
            for match in info["identifier_list"]:
                print(f"      - {match}")

    print("\nDone ✔")


if __name__ == "__main__":
    main()
