import re
import os
import json
from collections import defaultdict

def load_skill_mapping(skill_mapping_path):
    """
    Loads skill data from a JSON file. Identifiers are regex patterns.
    Returns: dict: skill_name -> list of regex patterns
    """
    try:
        if not os.path.exists(skill_mapping_path):
            print(f"Error: Skill mapping file not found at {skill_mapping_path}")
            return None

        with open(skill_mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        processed_mapping = {}
        for skill_entry in data:
            skill_name = skill_entry["skill"]
            patterns = skill_entry["identifiers"]
            processed_mapping[skill_name] = patterns
            
        return processed_mapping

    except Exception as e:
        print(f"Error loading skill mapping: {e}")
        return None


def analyze_code_file(file_path, skill_mapping_path):
    """
    Analyzes a code file and returns skill occurrence counts and density.
    """
    skill_mapping = load_skill_mapping(skill_mapping_path)
    if skill_mapping is None:
        return {"error": "Skill mapping failed to load. Analysis aborted."}
        
    if not os.path.exists(file_path):
        return {"error": f"Code file not found: {file_path}"}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        return {"error": f"Error reading code file: {e}"}

    # Remove Java comments (single-line and multi-line)
    code_cleaned = re.sub(r'//.*|/\*[\s\S]*?\*/', '', code_content)

    # Count non-empty lines for NCLOC
    non_empty_lines = [line for line in code_cleaned.splitlines() if line.strip()]
    loc = len(non_empty_lines)

    # Skill analysis
    skill_scores = defaultdict(lambda: {"raw_count": 0, "identifier_list": []})

    for skill, patterns in skill_mapping.items():
        count = 0
        for pattern in patterns:
            try:
                matches = re.findall(pattern, code_cleaned, flags=re.MULTILINE)
                match_count = len(matches)
            except re.error as e:
                print(f"Regex Error for skill '{skill}' pattern '{pattern}': {e}")
                continue

            if match_count > 0:
                skill_scores[skill]["identifier_list"].append(f"'{pattern}' ({match_count})")
                count += match_count

        skill_scores[skill]["raw_count"] = count
        skill_scores[skill]["density_score"] = round(count / loc * 100, 4) if loc > 0 else 0

    return {
        "total_lines_of_code": loc,
        "skill_scores": dict(skill_scores)
    }