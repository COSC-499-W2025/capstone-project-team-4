from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .contribution_ranking import ProjectContributionSummary


LOG_FILENAME = "project_contributions_log.json"


def _get_log_path(outputs_dir: Path | None = None) -> Path:
    project_root = Path(__file__).resolve().parents[2]

    # fixed outputs directory
    fixed_outputs = project_root / "outputs"
    fixed_outputs.mkdir(parents=True, exist_ok=True)

    return fixed_outputs / LOG_FILENAME


def append_contribution_entry(
    summary: ProjectContributionSummary,
    *,
    outputs_dir: Path | None = None,
    extra: Dict[str, Any] | None = None,
) -> None: # Makes a single contribution summary to the log file. - summary: the ProjectContributionSummary from rank_projects_for_contributor()
    log_path = _get_log_path(outputs_dir)

    # Load existing log (if any)
    if log_path.exists():
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            data = []
    else:
        data = []

    entry = asdict(summary)
    entry["logged_at"] = datetime.utcnow().isoformat() + "Z"

    if extra:
        entry.update(extra)

    data.append(entry)

    log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_log(outputs_dir: Path | None = None) -> List[Dict[str, Any]]:
    # Load all log entries as a list of dicts.
    log_path = _get_log_path(outputs_dir)
    if not log_path.exists():
        return []
    try:
        return json.loads(log_path.read_text(encoding="utf-8"))
    except Exception:
        return []


def rank_projects_from_log( # Rank projects for a given contributor based on entries in the log file. Returns a list of entries grouped by (project_root, identifier, match_by), sorted by contribution_score (descending).
    identifier: str,
    match_by: str = "email",   # "email" or "name"
    *,
    outputs_dir: Path | None = None,
) -> List[Dict[str, Any]]:
    
    entries = load_log(outputs_dir)

    # Filter entries for this contributor
    filtered = [
        e for e in entries
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
