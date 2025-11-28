from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Literal, Dict, Any

from .project_analyzer import analyze_contributors  # uses your existing git analyzer


ContributorMatchField = Literal["name", "email"]


@dataclass
class ProjectContributionSummary:
    """
    A summary of one contributor's impact within a single project.
    """
    project_root: str
    identifier: str            # the resolved name or email used to identify the contributor
    match_by: ContributorMatchField

    commits: int
    total_lines_added: int
    total_lines_deleted: int
    files_touched: int

    contribution_score: float  # combined score used for ranking


def compute_contribution_score(
    contributor: Dict[str, Any],
    *,
    weight_commits: float = 1.0,
    weight_lines_changed: float = 0.01,
    weight_files_touched: float = 0.1,
) -> float:
    """
    Compute a numeric score from a contributor record returned by analyze_contributors().

    You can tweak the weights depending on how you want to value:
      - number of commits
      - how many lines changed
      - how many files they touched
    """
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
    """
    Find a contributor in the list by name or email (case-insensitive).

    `contributors` is the list returned by analyze_contributors().
    """
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
            Iterable of paths to project roots (directories that contain a .git repo).
        match_by:
            "name" or "email" — how to identify the contributor in analyze_contributors() output.
        identifier:
            The exact name or email to match (case-insensitive).
        score_kwargs:
            Optional dict of overrides for compute_contribution_score() weights, e.g.:
            { "weight_commits": 1.0, "weight_lines_changed": 0.02 }

    Returns:
        List[ProjectContributionSummary], sorted from highest contribution_score to lowest.
    """
    if score_kwargs is None:
        score_kwargs = {}

    summaries: List[ProjectContributionSummary] = []

    for root in project_roots:
        root_path = Path(root)
        # Use your existing git analysis function (local .git history)
        contributors = analyze_contributors(str(root_path), use_all_branches=True)  # type: ignore[arg-type]
        # contributors is a list of dicts with name, primary_email, commits, etc. :contentReference[oaicite:0]{index=0}

        contributor = _find_contributor(
            contributors,
            match_by=match_by,
            value=identifier,
        )

        # If this person didn't contribute to this project, skip it
        if contributor is None:
            continue

        score = compute_contribution_score(contributor, **score_kwargs)

        summary = ProjectContributionSummary(
            project_root=str(root_path.resolve()),
            identifier=(
                contributor.get("primary_email")
                if match_by == "email"
                else contributor.get("name", "")
            ),
            match_by=match_by,
            commits=contributor.get("commits", 0),
            total_lines_added=contributor.get("total_lines_added", 0),
            total_lines_deleted=contributor.get("total_lines_deleted", 0),
            files_touched=len(contributor.get("files_modified", {}) or {}),
            contribution_score=score,
        )

        summaries.append(summary)

    # Sort projects: highest contribution score first
    summaries.sort(key=lambda s: s.contribution_score, reverse=True)
    return summaries

def merge_contributors(contributors, aliases):
    
    merged = {
        "name": "Merged User",
        "primary_email": aliases[0][1],
        "commits": 0,
        "total_lines_added": 0,
        "total_lines_deleted": 0,
        "files_modified": {},
    }

    for match_by, value in aliases:
        c = _find_contributor(contributors, match_by=match_by, value=value)
        if not c:
            continue
        merged["commits"] += c.get("commits", 0)
        merged["total_lines_added"] += c.get("total_lines_added", 0)
        merged["total_lines_deleted"] += c.get("total_lines_deleted", 0)
        for f, count in (c.get("files_modified") or {}).items():
            merged["files_modified"][f] = merged["files_modified"].get(f, 0) + count

    return merged



def summarize_top_projects(
    ranked_projects: List[ProjectContributionSummary],
    top_n: int = 3,
) -> List[str]:
    """
    Turn the top N ranked projects into human-readable text summaries.

    This is convenient for printing to console, logs, or feeding into a UI.
    """
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
            f"  Files touched: {p.files_touched}"
        )
        summaries.append(text)

    return summaries
