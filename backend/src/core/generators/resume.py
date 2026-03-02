"""
Resume item generation module.

Generates resume-ready bullet points for a project using AI.

Migrated from src/core/resume_item_generator.py
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


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
    Pick the main contributor based on commit percentage.

    Args:
        contributors: List of contributor dictionaries

    Returns:
        The contributor with highest commit percentage, or empty dict
    """
    if not contributors:
        return {}
    return max(contributors, key=lambda c: c.get("commit_percent", 0))


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


def _build_ai_context(
    project_name: str,
    contributors: List[Dict[str, Any]],
    project_stats: Dict[str, Any],
    skill_categories: Dict[str, List[str]],
    languages: List[str],
    frameworks: List[str],
    libraries: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    complexity_dict: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build context string for AI resume generation.

    Args:
        project_name: Name of the project
        contributors: List of contributor statistics
        project_stats: Project statistics dictionary
        skill_categories: Dictionary of skill categories to skill lists
        languages: List of programming languages
        frameworks: List of frameworks
        libraries: Optional list of libraries
        tools: Optional list of tools
        complexity_dict: Optional complexity analysis results

    Returns:
        Formatted context string for AI
    """
    libraries = libraries or []
    tools = tools or []

    # Tech stack
    tech_stack = extract_tech_stack(languages, frameworks, skill_categories)

    # Contributor stats
    main = pick_main_contributor(contributors)
    commit_percent = main.get("commit_percent", 0) or 0
    added = main.get("total_lines_added", 0) or 0
    commits = main.get("commits", 0) or 0

    # Project stats
    file_count = project_stats.get("total_files", 0) or 0
    total_lines = project_stats.get("total_lines", 0) or 0

    # Complexity
    avg_cx = 0
    max_cx = 0
    total_functions = 0
    if complexity_dict and complexity_dict.get("functions"):
        values = [fn["cyclomatic_complexity"] for fn in complexity_dict["functions"]]
        if values:
            avg_cx = sum(values) / len(values)
            max_cx = max(values)
            total_functions = len(values)

    context = f"""Project: {project_name}

Technical Stack:
- Languages: {', '.join(languages) if languages else 'N/A'}
- Frameworks: {', '.join(frameworks) if frameworks else 'N/A'}
- Libraries: {', '.join(libraries[:10]) if libraries else 'N/A'}
- Tools: {', '.join(tools[:10]) if tools else 'N/A'}
- Key Technologies: {', '.join(tech_stack[:15])}

Project Metrics:
- Total Files: {file_count}
- Total Lines of Code: {total_lines:,}
- Total Functions Analyzed: {total_functions}
- Average Cyclomatic Complexity: {avg_cx:.1f}
- Maximum Cyclomatic Complexity: {max_cx}

Contribution:
- Contribution Percentage: {commit_percent:.1f}%
- Lines Added: {added:,}
- Total Commits: {commits}
- Total Contributors: {len(contributors)}

Skill Categories:
{chr(10).join(f"- {cat}: {', '.join(skills[:5])}" for cat, skills in skill_categories.items() if skills)}
"""
    return context


def _generate_with_ai(
    project_name: str,
    context: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> Dict[str, Any]:
    """
    Generate resume item using OpenAI API.

    Args:
        project_name: Name of the project
        context: Formatted context string
        api_key: OpenAI API key
        model: AI model to use
        temperature: AI temperature parameter
        max_tokens: Maximum tokens for response

    Returns:
        Dictionary with 'title' and 'highlights' keys

    Raises:
        Exception: If AI generation fails
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        system_prompt = """You are a professional resume writer specializing in technical resumes for software engineers.
Your task is to generate concise, impactful resume bullet points that highlight technical achievements and skills.

Guidelines:
- Generate exactly 3 bullet points
- Start each bullet with an action verb (Developed, Built, Implemented, Designed, etc.)
- Quantify achievements with metrics when available
- Highlight technical stack and complexity
- Keep each bullet to 1-2 lines maximum
- Use professional, achievement-oriented language
- Do NOT include bullet symbols (•, -, *) - just the text
- Focus on what was accomplished, not just what was done"""

        user_prompt = f"""Based on the following project analysis data, generate 3 professional resume bullet points:

{context}

Provide the response in this exact format:
BULLET1: [first bullet point text]
BULLET2: [second bullet point text]
BULLET3: [third bullet point text]"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content.strip()

        # Parse bullet points
        highlights = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("BULLET"):
                # Extract text after "BULLET1: " or similar
                bullet_text = line.split(":", 1)[1].strip() if ":" in line else line
                highlights.append(bullet_text)

        # Fallback if parsing failed
        if len(highlights) < 3:
            logger.warning("AI response parsing failed, using full response")
            highlights = [line.strip() for line in content.split("\n") if line.strip() and not line.startswith("BULLET")]
            highlights = highlights[:3]  # Take first 3 lines

        return {"title": project_name, "highlights": highlights}

    except Exception as e:
        logger.error(f"AI resume generation failed: {e}")
        raise


def _generate_template_based(
    project_name: str,
    contributors: List[Dict[str, Any]],
    project_stats: Dict[str, Any],
    skill_categories: Dict[str, List[str]],
    languages: List[str],
    frameworks: List[str],
    complexity_dict: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate resume item using template-based approach (fallback).

    Args:
        project_name: Name of the project
        contributors: List of contributor statistics
        project_stats: Project statistics dictionary
        skill_categories: Dictionary of skill categories to skill lists
        languages: List of programming languages
        frameworks: List of frameworks
        complexity_dict: Optional complexity analysis results

    Returns:
        Dictionary with 'title' and 'highlights' keys
    """
    # -------- Tech stack --------
    tech_stack = extract_tech_stack(languages, frameworks, skill_categories)
    tech_str = format_list_with_and(tech_stack[:8])  # Natural language formatting

    # -------- Top contributor --------
    main = pick_main_contributor(contributors)
    commit_percent = main.get("commit_percent", 0) or 0
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

    if commit_percent > 0 or added > 0:
        highlights.append(
            f"Owned {commit_percent:.1f}% of project contributions with {added:,} lines added, demonstrating feature ownership and collaborative Git workflow."
        )
    else:
        highlights.append(
            "Collaborated through Git version control using iterative feature development and structured code reviews."
        )

    return {"title": project_name, "highlights": highlights}


def generate_resume_item(
    project_name: str,
    contributors: List[Dict[str, Any]],
    project_stats: Dict[str, Any],
    skill_categories: Dict[str, List[str]],
    *,
    languages: Optional[List[str]] = None,
    frameworks: Optional[List[str]] = None,
    libraries: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    complexity_dict: Optional[Dict[str, Any]] = None,
    use_ai: bool = True,
    api_key: Optional[str] = None,
    ai_model: str = "gpt-4o-mini",
    ai_temperature: float = 0.7,
    ai_max_tokens: int = 500,
) -> Dict[str, Any]:
    """
    Generate a resume-ready item for a project using AI or template-based approach.

    Args:
        project_name: Name of the project
        contributors: List of contributor statistics
        project_stats: Project statistics dictionary
        skill_categories: Dictionary of skill categories to skill lists
        languages: Optional list of programming languages
        frameworks: Optional list of frameworks
        libraries: Optional list of libraries
        tools: Optional list of tools
        complexity_dict: Optional complexity analysis results
        use_ai: Whether to use AI generation (requires api_key)
        api_key: OpenAI API key (if None, falls back to template)
        ai_model: AI model to use
        ai_temperature: AI temperature parameter
        ai_max_tokens: Maximum tokens for AI response

    Returns:
        Dictionary with 'title' and 'highlights' keys
    """
    languages = languages or []
    frameworks = frameworks or []
    libraries = libraries or []
    tools = tools or []

    # Try AI generation if enabled and API key provided
    if use_ai and api_key:
        try:
            logger.info(f"Attempting AI resume generation with model '{ai_model}'")
            context = _build_ai_context(
                project_name=project_name,
                contributors=contributors,
                project_stats=project_stats,
                skill_categories=skill_categories,
                languages=languages,
                frameworks=frameworks,
                libraries=libraries,
                tools=tools,
                complexity_dict=complexity_dict,
            )

            result = _generate_with_ai(
                project_name=project_name,
                context=context,
                api_key=api_key,
                model=ai_model,
                temperature=ai_temperature,
                max_tokens=ai_max_tokens,
            )

            logger.info(f"Generated AI resume for '{project_name}'")
            return result

        except Exception as e:
            logger.warning(f"AI generation failed, falling back to template: {e}")
    else:
        if not use_ai:
            logger.info("AI resume generation disabled via settings")
        if not api_key:
            logger.info("No OPENAI_API_KEY configured, using template-based generation")

    # Fallback to template-based generation
    logger.info(f"Using template-based resume generation for '{project_name}'")
    return _generate_template_based(
        project_name=project_name,
        contributors=contributors,
        project_stats=project_stats,
        skill_categories=skill_categories,
        languages=languages,
        frameworks=frameworks,
        complexity_dict=complexity_dict,
    )
