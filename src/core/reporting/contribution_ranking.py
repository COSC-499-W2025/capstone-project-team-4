from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Literal, Dict, Any

from ..analyzer.project_analyzer import analyze_contributors  # uses your existing git analyzer


ContributorMatchField = Literal["name", "email"]


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


def _find_contributor( #Find a contributor in the list by name or email (case-insensitive). `contributors` is the list returned by analyze_contributors().
    
    contributors: List[Dict[str, Any]],
    *,
    match_by: ContributorMatchField,
    value: str,
) -> Optional[Dict[str, Any]]:
    
    
    value_lower = value.lower()

    for c in contributors:
        if match_by == "name":
            if c.get("name", "").lower() == value_lower:
                return c
        elif match_by == "email":
            if c.get("primary_email", "").lower() == value_lower:
                return c

    return None



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
