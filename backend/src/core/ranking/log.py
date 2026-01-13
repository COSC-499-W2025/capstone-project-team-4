"""
Project contribution logging module.

Provides functionality to log and retrieve contribution data.

Migrated from src/core/project_contribution_log.py
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.core.ranking.contribution import ProjectContributionSummary

logger = logging.getLogger(__name__)

LOG_FILENAME = "project_contributions_log.json"


def _get_log_path(outputs_dir: Optional[Path] = None) -> Path:
    """
    Get the path to the contribution log file.

    Args:
        outputs_dir: Optional custom outputs directory

    Returns:
        Path to the log file
    """
    project_root = Path(__file__).resolve().parents[3]

    # Fixed outputs directory
    fixed_outputs = project_root / "outputs"
    fixed_outputs.mkdir(parents=True, exist_ok=True)

    return fixed_outputs / LOG_FILENAME


def append_contribution_entry(
    summary: ProjectContributionSummary,
    *,
    outputs_dir: Optional[Path] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Append a single contribution summary to the log file.

    Args:
        summary: The ProjectContributionSummary from rank_projects_for_contributor()
        outputs_dir: Optional custom outputs directory
        extra: Optional extra data to include in the log entry
    """
    log_path = _get_log_path(outputs_dir)

    # Load existing log (if any)
    if log_path.exists():
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Could not load existing log: %s", e)
            data = []
    else:
        data = []

    entry = asdict(summary)
    entry["logged_at"] = datetime.utcnow().isoformat() + "Z"

    if extra:
        entry.update(extra)

    data.append(entry)

    log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_log(outputs_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load all log entries as a list of dicts.

    Args:
        outputs_dir: Optional custom outputs directory

    Returns:
        List of log entry dictionaries
    """
    log_path = _get_log_path(outputs_dir)
    if not log_path.exists():
        return []
    try:
        return json.loads(log_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Could not load log: %s", e)
        return []


def rank_projects_from_log(
    identifier: str,
    match_by: str = "email",
    *,
    outputs_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Rank projects for a given contributor based on entries in the log file.

    Returns a list of entries grouped by (project_root, identifier, match_by),
    sorted by contribution_score (descending).

    Args:
        identifier: The name or email of the contributor
        match_by: "email" or "name"
        outputs_dir: Optional custom outputs directory

    Returns:
        Ranked list of contribution entries
    """
    entries = load_log(outputs_dir)

    # Filter entries for this contributor
    filtered = [
        e
        for e in entries
        if e.get("identifier", "").lower() == identifier.lower()
        and e.get("match_by") == match_by
    ]

    if not filtered:
        return []

    # For each project_root, keep the highest score we've logged
    best_by_project: Dict[str, Dict[str, Any]] = {}
    for e in filtered:
        proj = e["project_root"]
        score = e.get("contribution_score", 0)
        current = best_by_project.get(proj)
        if current is None or score > current.get("contribution_score", 0):
            best_by_project[proj] = e

    # Sort projects by score descending
    ranked = sorted(
        best_by_project.values(),
        key=lambda x: x.get("contribution_score", 0),
        reverse=True,
    )

    return ranked
