from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Literal, Dict, Any

from ..analyzer.project_analyzer import analyze_contributors  # uses your existing git analyzer


ContributorMatchField = Literal["name", "email", "username", "any"]


@dataclass
class ProjectContributionSummary: #A summary of one contributor's impact within a single project.
    
    project_root: str
    identifier: str            # the name or email used to identify the contributor
    match_by: ContributorMatchField

    commits: int
    total_lines_added: int
    total_lines_deleted: int
    files_touched: int

    contribution_score: float  # combined score used for ranking


def compute_contribution_score( # Compute a numeric score from a contributor record returned by analyze_contributors(). Weight is based on number of commits and lines changed and files touched.
    
    contributor: Dict[str, Any],
    *,
    weight_commits: float = 1.0,
    weight_lines_changed: float = 0.005,
    weight_files_touched: float = 0.1,
) -> float:
    
    commits = contributor.get("commits", 0)
    added = contributor.get("total_lines_added", 0)
    deleted = contributor.get("total_lines_deleted", 0)
    files_touched = len(contributor.get("files_modified", {}) or {})

    lines_changed = added + deleted

    return (
        commits * weight_commits
        + lines_changed * weight_lines_changed
        + files_touched * weight_files_touched
    )


def _find_contributor(
    contributors: List[Dict[str, Any]],
    *,
    match_by: ContributorMatchField,
    value: str,
) -> Optional[Dict[str, Any]]:
    """Find a contributor by name, email, username, or any field (case-insensitive).
    
    Args:
        contributors: List returned by analyze_contributors()
        match_by: Field to match against ('name', 'email', 'username', 'any')
        value: Value to search for
        
    Returns:
        Matching contributor dict or None if not found
    """
    value_lower = value.lower()

    for c in contributors:
        if match_by == "name":
            if c.get("name", "").lower() == value_lower:
                return c
        elif match_by == "email":
            # Check primary email
            if c.get("primary_email", "").lower() == value_lower:
                return c
            # Check all_emails if available
            all_emails = c.get("all_emails", [])
            for email in all_emails:
                if isinstance(email, str) and email.lower() == value_lower:
                    return c
        elif match_by == "username":
            # Check for username in various fields
            username = c.get("username", "").lower()
            if username == value_lower:
                return c
            # Also check if the value appears in the name or email
            name = c.get("name", "").lower()
            if value_lower in name or name in value_lower:
                return c
        elif match_by == "any":
            # Check all possible fields
            fields_to_check = [
                c.get("name", ""),
                c.get("primary_email", ""),
                c.get("username", "")
            ]
            # Add all emails
            all_emails = c.get("all_emails", [])
            fields_to_check.extend(str(email) for email in all_emails if isinstance(email, str))
            
            # Check exact matches first
            for field in fields_to_check:
                if field.lower() == value_lower:
                    return c
            
            # Then check partial matches (for usernames that might appear in names)
            for field in fields_to_check:
                if field and (value_lower in field.lower() or field.lower() in value_lower):
                    return c

    return None


def _find_similar_contributors(
    contributors: List[Dict[str, Any]],
    value: str,
    max_suggestions: int = 5
) -> List[Dict[str, Any]]:
    """Find contributors with similar names/emails for suggestions."""
    value_lower = value.lower()
    suggestions = []
    
    for c in contributors:
        # Check if any field contains the search value or vice versa
        fields = [
            c.get("name", ""),
            c.get("primary_email", ""),
            c.get("username", "")
        ]
        
        # Add all emails
        all_emails = c.get("all_emails", [])
        fields.extend(str(email) for email in all_emails if isinstance(email, str))
        
        for field in fields:
            if field and (value_lower in field.lower() or field.lower() in value_lower):
                if c not in suggestions:
                    suggestions.append(c)
                break
    
    return suggestions[:max_suggestions]



def rank_projects_for_contributor(
    project_roots: Iterable[str | Path],
    *,
    match_by: ContributorMatchField,
    identifier: str,
    score_kwargs: Optional[Dict[str, float]] = None,
) -> List[ProjectContributionSummary]:
    """
Rank multiple projects by how important they were for a specific contributor.

Args:
    project_roots:
        Iterable of paths to project directories (each containing a .git folder).
    match_by:
        Either "name" or "email" – determines how the contributor is identified.
    identifier:
        The exact name or email value to match (case-insensitive).
    score_kwargs:
        Optional scoring keyword arguments passed directly into
        compute_contribution_score(), allowing custom weights.

Scoring Formula:
    contribution_score =
        commits * weight_commits
        + (total_lines_added + total_lines_deleted) * weight_lines_changed
        + files_touched * weight_files_touched

Default Weights:
    weight_commits = 1.0
    weight_lines_changed = 0.005
    weight_files_touched = 0.1

The higher the score, the more significant the contributor's impact
on that project.
"""
    if score_kwargs is None: 
        score_kwargs = {}

    summaries: List[ProjectContributionSummary] = []

    for root in project_roots:
        root_path = Path(root)

        # use default branch only
        contributors = analyze_contributors(
            str(root_path)
        )  # type: ignore[arg-type]

        contributor = _find_contributor(
            contributors,
            match_by=match_by,
            value=identifier,
        )

        if contributor is None:
            # Try fuzzy matching if exact match fails
            if match_by != "any":
                contributor = _find_contributor(
                    contributors,
                    match_by="any",
                    value=identifier,
                )
            
            if contributor is None:
                continue

        resolved_identifier = (
            contributor.get("primary_email")
            if match_by == "email"
            else contributor.get("name", "")
        )
        resolved_match_by = match_by

        score = compute_contribution_score(contributor, **score_kwargs)

        summaries.append(
            ProjectContributionSummary(
                project_root=str(root_path.resolve()),
                identifier=resolved_identifier,
                match_by=resolved_match_by,
                commits=contributor.get("commits", 0),
                total_lines_added=contributor.get("total_lines_added", 0),
                total_lines_deleted=contributor.get("total_lines_deleted", 0),
                files_touched=len(contributor.get("files_modified", {}) or {}),
                contribution_score=score,
            )
        )

    summaries.sort(key=lambda s: s.contribution_score, reverse=True)
    return summaries


def summarize_top_projects( # Turn the top N ranked projects into human-readable text summaries.
    ranked_projects: List[ProjectContributionSummary],
    top_n: int = 3,
) -> List[str]:
    
    
    summaries: List[str] = []

    for p in ranked_projects[:top_n]:
        lines_changed = p.total_lines_added + p.total_lines_deleted

        text = (
            f"Project: {p.project_root}\n"
            f"  Contributor ({p.match_by}): {p.identifier}\n"
            f"  Contribution score: {p.contribution_score:.2f}\n"
            f"  Commits: {p.commits}\n"
            f"  Lines changed: +{p.total_lines_added} / -{p.total_lines_deleted} "
            f"(total {lines_changed})\n"
            f"  Files touched: {p.files_touched}\n"
            f"  This score is based on the number of commits, total lines changed, "
            f"and the number of files touched by this contributor."
        )
        summaries.append(text)

    return summaries


def get_available_contributors(
    project_root: str | Path
) -> List[Dict[str, str]]:
    """Get list of available contributors with their identifiers for user reference.
    
    Returns:
        List of dicts with contributor info: name, email, username
    """
    contributors = analyze_contributors(str(project_root))
    
    result = []
    for c in contributors:
        info = {
            "name": c.get("name", ""),
            "primary_email": c.get("primary_email", ""),
            "username": c.get("username", ""),
            "commits": c.get("commits", 0),
        }
        # Add all emails for completeness
        all_emails = c.get("all_emails", [])
        if all_emails:
            info["all_emails"] = [str(email) for email in all_emails if isinstance(email, str)]
        
        result.append(info)
    
    # Sort by number of commits (most active first)
    result.sort(key=lambda x: x["commits"], reverse=True)
    return result


def find_contributor_suggestions(
    project_root: str | Path,
    search_value: str,
    max_suggestions: int = 3
) -> List[Dict[str, str]]:
    """Find similar contributors when exact match fails.
    
    Args:
        project_root: Path to git repository
        search_value: The value that failed to match
        max_suggestions: Maximum number of suggestions to return
        
    Returns:
        List of similar contributors with their info
    """
    contributors = analyze_contributors(str(project_root))
    similar = _find_similar_contributors(contributors, search_value, max_suggestions)
    
    result = []
    for c in similar:
        info = {
            "name": c.get("name", ""),
            "primary_email": c.get("primary_email", ""),
            "username": c.get("username", ""),
            "commits": c.get("commits", 0),
        }
        result.append(info)
    
    return result
