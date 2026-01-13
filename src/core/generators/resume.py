"""
Resume item generation module.

Generates resume-ready bullet points for a project.

Migrated from src/core/resume_item_generator.py
"""

from typing import Dict, List, Any, Optional


def extract_tech_stack(
    languages: List[str],
    frameworks: List[str],
    skill_categories: Dict[str, List[str]],
) -> List[str]:
    """
    Extract a unified tech stack from languages, frameworks, and skills.

    Args:
        languages: List of programming languages
        frameworks: List of frameworks
        skill_categories: Dictionary of skill categories to skill lists

    Returns:
        Sorted, unique list of technologies
    """
    tech = []

    if languages:
        tech.extend(languages)
    if frameworks:
        tech.extend(frameworks)

    # Include only top 2 skills per category - resume-friendly
    for _, skills in skill_categories.items():
        tech.extend(skills[:2])

    # Unique + sorted
    return sorted(set(tech))


def pick_main_contributor(contributors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Pick the main contributor based on contribution percentage.

    Args:
        contributors: List of contributor dictionaries

    Returns:
        The contributor with highest percentage, or empty dict
    """
    if not contributors:
        return {}
    return max(contributors, key=lambda c: c.get("percent", 0))


def format_list_with_and(items: List[str]) -> str:
    """
    Format a list with proper grammar.

    Args:
        items: List of strings to format

    Returns:
        'x', 'x and y', or 'x, y and z' formatted string
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    *start, last = items
    return f"{', '.join(start)} and {last}"


def generate_resume_item(
    project_name: str,
    contributors: List[Dict[str, Any]],
    project_stats: Dict[str, Any],
    skill_categories: Dict[str, List[str]],
    *,
    languages: Optional[List[str]] = None,
    frameworks: Optional[List[str]] = None,
    complexity_dict: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a resume-ready item for a project.

    Args:
        project_name: Name of the project
        contributors: List of contributor statistics
        project_stats: Project statistics dictionary
        skill_categories: Dictionary of skill categories to skill lists
        languages: Optional list of programming languages
        frameworks: Optional list of frameworks
        complexity_dict: Optional complexity analysis results

    Returns:
        Dictionary with 'title' and 'highlights' keys
    """
    languages = languages or []
    frameworks = frameworks or []

    # -------- Tech stack --------
    tech_stack = extract_tech_stack(languages, frameworks, skill_categories)
    tech_str = format_list_with_and(tech_stack[:8])  # Natural language formatting

    # -------- Top contributor --------
    main = pick_main_contributor(contributors)
    percent = main.get("percent", 0) or 0
    added = main.get("total_lines_added", 0) or 0

    # -------- Project stats --------
    file_count = project_stats.get("total_files", 0) or 0

    # -------- Complexity summary --------
    avg_cx = 0
    max_cx = 0
    if complexity_dict and complexity_dict.get("functions"):
        values = [fn["cyclomatic_complexity"] for fn in complexity_dict["functions"]]
        if values:
            avg_cx = sum(values) / len(values)
            max_cx = max(values)

    highlights = []

    highlights.append(f"Developed {project_name} using {tech_str}.")

    if file_count > 0 and (avg_cx > 0 or max_cx > 0):
        highlights.append(
            f"Analyzed {file_count} source files with an average cyclomatic complexity of {avg_cx:.1f} (max {max_cx})."
        )

    if percent > 0 or added > 0:
        highlights.append(
            f"Owned {percent:.1f}% of project contributions with {added:,} lines added, demonstrating feature ownership and collaborative Git workflow."
        )
    else:
        highlights.append(
            "Collaborated through Git version control using iterative feature development and structured code reviews."
        )

    # Apply actual bullet-point text style
    highlights = [f"• {h}" for h in highlights]

    return {"title": project_name, "highlights": highlights}
