"""
Generate résumé-ready bullet points for a project.
Outputs:
{
    "title": "...",
    "highlights": [ "...", "...", ... ]
}
"""
def extract_tech_stack(languages, frameworks, skill_categories):
    tech = []

    if languages:
        tech.extend(languages)
    if frameworks:
        tech.extend(frameworks)

    # include only top 2 skills per category — resume-friendly
    for _, skills in skill_categories.items():
        tech.extend(skills[:2])

    # unique + sorted
    return sorted(set(tech))


def pick_main_contributor(contributors):
    if not contributors:
        return {}
    return max(contributors, key=lambda c: c.get("percent", 0))


def format_list_with_and(items):
    """Return 'x', 'x and y', 'x, y and z'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    *start, last = items
    return f"{', '.join(start)} and {last}"


def generate_resume_item(
    project_name,
    contributors,
    project_stats,
    skill_categories,
    *,
    languages=None,
    frameworks=None,
    complexity_dict=None
):
    languages = languages or []
    frameworks = frameworks or []

    # -------- Tech stack --------
    tech_stack = extract_tech_stack(languages, frameworks, skill_categories)
    tech_str = format_list_with_and(tech_stack[:8])   # natural language formatting

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

    highlights.append(
        f"Developed {project_name} using {tech_str}."
    )

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

    return {
        "title": project_name,
        "highlights": highlights
    }
