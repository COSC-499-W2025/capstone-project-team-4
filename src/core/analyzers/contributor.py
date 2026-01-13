"""
Git contributor analysis module.

Simplified implementation for fast contributor extraction.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional

try:
    from git import Repo, InvalidGitRepositoryError
except ImportError:
    Repo = None
    InvalidGitRepositoryError = Exception

logger = logging.getLogger(__name__)

# Maximum commits to analyze (None = unlimited)
MAX_COMMITS = 500


def analyze_contributors(
    project_path: str = ".",
    use_all_branches: bool = False,
    max_commits: Optional[int] = MAX_COMMITS
) -> List[Dict[str, Any]]:
    """
    Analyze Git commit history and extract contributor statistics.

    Args:
        project_path: Path to the Git repository
        use_all_branches: If True, analyze all branches
        max_commits: Maximum commits to process (None = unlimited)

    Returns:
        List of contributor dictionaries with stats
    """
    if Repo is None:
        logger.warning("GitPython not installed")
        return []

    # Open repository
    try:
        repo = Repo(project_path)
    except InvalidGitRepositoryError:
        logger.warning("Not a git repository: %s", project_path)
        return []
    except Exception as e:
        logger.warning("Error opening repository: %s", e)
        return []

    # Collect contributors in single pass
    contributors: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "name": "",
        "email": "",
        "commits": 0,
        "history": [],
        "total_lines_added": 0,
        "total_lines_deleted": 0,
        "files_modified": {},
    })

    try:
        commit_iter = repo.iter_commits("--all" if use_all_branches else None)
        commit_count = 0

        for commit in commit_iter:
            # Enforce limit
            if max_commits and commit_count >= max_commits:
                logger.info(f"Reached commit limit ({max_commits}), stopping")
                break

            commit_count += 1

            # Extract author info
            try:
                name = commit.author.name.strip() if commit.author.name else "Unknown"
                email = commit.author.email.strip().lower() if commit.author.email else ""
            except Exception:
                continue

            # Skip bots
            if "[bot]" in name.lower():
                continue

            # Use email as key (simple deduplication)
            key = email or name.lower()

            # Update contributor
            contributors[key]["name"] = name
            contributors[key]["email"] = email
            contributors[key]["commits"] += 1

            # Add to history (minimal data)
            contributors[key]["history"].append({
                "hash": commit.hexsha[:8],
                "message": commit.message.strip()[:100] if commit.message else "",
                "timestamp": commit.committed_date,
            })

        logger.info(f"Processed {commit_count} commits, found {len(contributors)} contributors")

    except Exception as e:
        logger.warning("Error processing commits: %s", e)

    # Calculate percentages and format output
    total_commits = sum(c["commits"] for c in contributors.values())
    result = []

    for key, info in contributors.items():
        if total_commits > 0:
            info["percent"] = round((info["commits"] / total_commits) * 100, 2)
        else:
            info["percent"] = 0

        # Add compatibility fields
        info["primary_email"] = info["email"]
        info["github_email"] = info["email"] if "github" in info["email"] else None
        info["github_username"] = _extract_github_username(info["email"])

        result.append(info)

    # Sort by commits descending
    result.sort(key=lambda x: x["commits"], reverse=True)

    return result


def _extract_github_username(email: str) -> Optional[str]:
    """Extract GitHub username from noreply email."""
    if not email or "users.noreply.github.com" not in email:
        return None

    local_part = email.split("@")[0]
    if "+" in local_part:
        return local_part.split("+")[-1]
    return local_part
