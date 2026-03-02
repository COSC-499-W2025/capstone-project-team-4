"""
Portfolio generation module.

Generates a professional portfolio title and summary for a user
by aggregating data from all their analyzed projects.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def _build_ai_context(
    user_name: str,
    projects_data: List[Dict[str, Any]],
    aggregated_skills: Dict[str, List[str]],
    experiences: List[Dict[str, Any]],
    profile_summary: Optional[str] = None,
) -> str:
    """
    Build context string for AI portfolio generation.

    Args:
        user_name: Name of the user
        projects_data: List of project data dicts
        aggregated_skills: Skills grouped by category
        experiences: List of experience dicts
        profile_summary: Optional existing profile summary

    Returns:
        Formatted context string for AI
    """
    parts = [f"Portfolio for: {user_name}"]

    if profile_summary:
        parts.append(f"\nProfile Summary: {profile_summary}")

    # Projects
    parts.append(f"\nProjects ({len(projects_data)}):")
    for proj in projects_data:
        langs = ", ".join(proj.get("languages", [])) or "N/A"
        fws = ", ".join(proj.get("frameworks", [])) or "N/A"
        parts.append(f"- {proj['name']}: Languages: {langs}, Frameworks: {fws}")
        highlights = proj.get("resume_highlights", [])
        if highlights:
            parts.append(f"  Resume Highlights: {'; '.join(highlights[:3])}")

    # Aggregated skills
    if aggregated_skills:
        parts.append("\nAggregated Technical Skills:")
        for category, skills in aggregated_skills.items():
            if skills:
                parts.append(f"- {category}: {', '.join(skills[:10])}")

    # Experiences
    if experiences:
        parts.append("\nWork Experience:")
        for exp in experiences:
            end = exp.get("end_date") or "Present"
            parts.append(f"- {exp.get('job_title', 'N/A')} at {exp.get('company_name', 'N/A')} ({exp.get('start_date', 'N/A')} - {end})")
            if exp.get("description"):
                parts.append(f"  {exp['description'][:200]}")

    return "\n".join(parts)


def _generate_with_ai(
    context: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> Dict[str, str]:
    """
    Generate portfolio title and summary using OpenAI API.

    Args:
        context: Formatted context string
        api_key: OpenAI API key
        model: AI model to use
        temperature: AI temperature parameter
        max_tokens: Maximum tokens for response

    Returns:
        Dictionary with 'title' and 'summary' keys

    Raises:
        Exception: If AI generation fails
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        system_prompt = """You are a professional portfolio writer specializing in software engineering portfolios.
Your task is to generate a compelling portfolio title and summary that showcases the developer's
technical breadth, project experience, and professional growth.

Guidelines:
- Write a 3-5 sentence professional summary paragraph
- Highlight the developer's strongest technical areas based on project data
- Mention the breadth of projects and technologies
- Use professional, achievement-oriented language
- Write in paragraph form, no bullet points
- Focus on impact, breadth, and technical expertise

Provide the response in this exact format:
TITLE: [A professional portfolio title, e.g. "Full-Stack Software Engineer"]
SUMMARY: [The 3-5 sentence portfolio summary paragraph]"""

        user_prompt = f"""Based on the following developer portfolio data, generate a professional portfolio title and summary:

{context}

Provide the response in this exact format:
TITLE: [A professional portfolio title]
SUMMARY: [The 3-5 sentence portfolio summary paragraph]"""

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

        # Parse TITLE and SUMMARY
        title = "Software Engineering Portfolio"
        summary = ""

        for line in content.split("\n"):
            line = line.strip()
            if line.upper().startswith("TITLE:"):
                title = line.split(":", 1)[1].strip()
            elif line.upper().startswith("SUMMARY:"):
                summary = line.split(":", 1)[1].strip()

        # If SUMMARY wasn't on a single line, grab everything after the SUMMARY: line
        if not summary:
            in_summary = False
            summary_parts = []
            for line in content.split("\n"):
                if line.strip().upper().startswith("SUMMARY:"):
                    remainder = line.split(":", 1)[1].strip()
                    if remainder:
                        summary_parts.append(remainder)
                    in_summary = True
                elif in_summary and line.strip():
                    summary_parts.append(line.strip())
            summary = " ".join(summary_parts)

        # Final fallback: use the whole response as summary
        if not summary:
            summary = content

        return {"title": title, "summary": summary}

    except Exception as e:
        logger.error(f"AI portfolio generation failed: {e}")
        raise


def _generate_template_based(
    user_name: str,
    projects_data: List[Dict[str, Any]],
    aggregated_skills: Dict[str, List[str]],
) -> Dict[str, str]:
    """
    Generate portfolio title and summary using template (fallback).

    Args:
        user_name: Name of the user
        projects_data: List of project data dicts
        aggregated_skills: Skills grouped by category

    Returns:
        Dictionary with 'title' and 'summary' keys
    """
    # Collect all unique technologies
    all_langs = set()
    all_frameworks = set()
    for proj in projects_data:
        all_langs.update(proj.get("languages", []))
        all_frameworks.update(proj.get("frameworks", []))

    technologies = sorted(all_langs | all_frameworks)
    categories = sorted(aggregated_skills.keys())

    title = f"{user_name}'s Software Engineering Portfolio"

    parts = []
    parts.append(f"Software developer with experience across {len(projects_data)} project{'s' if len(projects_data) != 1 else ''}.")

    if technologies:
        tech_str = ", ".join(technologies[:8])
        parts.append(f"Proficient in {tech_str}.")

    if categories:
        cat_str = ", ".join(categories[:5])
        parts.append(f"Technical skills span {cat_str}.")

    summary = " ".join(parts)

    return {"title": title, "summary": summary}


def generate_portfolio(
    user_name: str,
    projects_data: List[Dict[str, Any]],
    aggregated_skills: Dict[str, List[str]],
    experiences: List[Dict[str, Any]],
    profile_summary: Optional[str] = None,
    *,
    use_ai: bool = True,
    api_key: Optional[str] = None,
    ai_model: str = "gpt-4o-mini",
    ai_temperature: float = 0.7,
    ai_max_tokens: int = 500,
) -> Dict[str, str]:
    """
    Generate a portfolio title and summary using AI or template-based approach.

    Args:
        user_name: Name of the user
        projects_data: List of project data dicts
        aggregated_skills: Skills grouped by category
        experiences: List of experience dicts
        profile_summary: Optional existing profile summary
        use_ai: Whether to use AI generation
        api_key: OpenAI API key
        ai_model: AI model to use
        ai_temperature: AI temperature parameter
        ai_max_tokens: Maximum tokens for AI response

    Returns:
        Dictionary with 'title' and 'summary' keys
    """
    if use_ai and api_key:
        try:
            logger.info("Attempting AI portfolio generation")
            context = _build_ai_context(
                user_name=user_name,
                projects_data=projects_data,
                aggregated_skills=aggregated_skills,
                experiences=experiences,
                profile_summary=profile_summary,
            )

            result = _generate_with_ai(
                context=context,
                api_key=api_key,
                model=ai_model,
                temperature=ai_temperature,
                max_tokens=ai_max_tokens,
            )

            logger.info("Generated AI portfolio successfully")
            return result

        except Exception as e:
            logger.warning(f"AI generation failed, falling back to template: {e}")
    else:
        if not use_ai:
            logger.info("AI portfolio generation disabled via settings")
        if not api_key:
            logger.info("No OPENAI_API_KEY configured, using template-based generation")

    logger.info("Using template-based portfolio generation")
    return _generate_template_based(
        user_name=user_name,
        projects_data=projects_data,
        aggregated_skills=aggregated_skills,
    )
