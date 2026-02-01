"""Test data snapshot routes."""

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.database import get_db
from src.models.schemas.test_data import (
    SnapshotArchive,
    SnapshotArchiveList,
    SnapshotComparison,
    SnapshotMetrics,
    MetricComparison,
)
from src.services.project_service import ProjectService

router = APIRouter(prefix="/test-data", tags=["test-data"])


@router.get("/snapshots", response_model=SnapshotArchiveList)
async def list_snapshot_archives():
    """List available test-data snapshot archives."""
    root_dir = settings.base_dir / "test-data" / "code-collab-proj-snapshots"
    if not root_dir.exists():
        raise HTTPException(status_code=404, detail="Snapshot directory not found.")

    items: list[SnapshotArchive] = []
    for zip_path in sorted(root_dir.glob("*.zip")):
        stat = zip_path.stat()
        items.append(
            SnapshotArchive(
                name=zip_path.name,
                relative_path=str(zip_path.relative_to(settings.base_dir)),
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            )
        )

    return SnapshotArchiveList(
        project_key="code-collab-proj",
        root_dir=str(root_dir.relative_to(settings.base_dir)),
        items=items,
    )


@router.get("/snapshots/compare", response_model=SnapshotComparison)
async def compare_snapshots(
    project1_id: int = Query(None, description="ID of first project"),
    project2_id: int = Query(None, description="ID of second project"),
    project1_name: str = Query(None, description="Name of first project"),
    project2_name: str = Query(None, description="Name of second project"),
    db: Session = Depends(get_db),
):
    """
    Compare two analyzed projects and return the differences.

    You can specify projects by ID or name:
    - By ID: ?project1_id=1&project2_id=2
    - By name: ?project1_name=Demo-Foundation&project2_name=Demo-Growth

    Returns:
    - Metrics for each project
    - Comparison of key metrics
    - What's new in the second project
    """
    service = ProjectService(db)

    # Retrieve first project
    if project1_id:
        project1 = service.get_project(project1_id)
    elif project1_name:
        project1 = service.get_project_by_name(project1_name)
    else:
        raise HTTPException(status_code=400, detail="Must provide either project1_id or project1_name")

    if not project1:
        raise HTTPException(status_code=404, detail=f"Project 1 not found")

    # Retrieve second project
    if project2_id:
        project2 = service.get_project(project2_id)
    elif project2_name:
        project2 = service.get_project_by_name(project2_name)
    else:
        raise HTTPException(status_code=400, detail="Must provide either project2_id or project2_name")

    if not project2:
        raise HTTPException(status_code=404, detail=f"Project 2 not found")

    # Convert to metrics
    metrics1 = _convert_to_snapshot_metrics(project1)
    metrics2 = _convert_to_snapshot_metrics(project2)

    # Calculate comparisons
    def calc_change(val1, val2):
        """Calculate numeric change and percent change."""
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            change = val2 - val1
            percent_change = ((val2 - val1) / val1 * 100) if val1 > 0 else None
            return change, percent_change
        return None, None

    # Contributors comparison
    contrib_change, contrib_percent = calc_change(metrics1.contributor_count, metrics2.contributor_count)

    # Languages comparison
    lang_change, lang_percent = calc_change(len(metrics1.languages), len(metrics2.languages))
    new_languages = list(set(metrics2.languages) - set(metrics1.languages))

    # Frameworks comparison
    fw_change, fw_percent = calc_change(len(metrics1.frameworks), len(metrics2.frameworks))
    new_frameworks = list(set(metrics2.frameworks) - set(metrics1.frameworks))

    # Libraries comparison
    lib_change, lib_percent = calc_change(len(metrics1.libraries), len(metrics2.libraries))
    new_libraries = list(set(metrics2.libraries) - set(metrics1.libraries))

    # Skills comparison
    skill_change, skill_percent = calc_change(metrics1.skill_count, metrics2.skill_count)

    # Files comparison
    files_change, files_percent = calc_change(metrics1.total_files, metrics2.total_files)

    # LOC comparison
    loc_change, loc_percent = calc_change(metrics1.total_loc, metrics2.total_loc)

    # Complexity comparison
    complexity_change, complexity_percent = calc_change(
        metrics1.avg_complexity or 0,
        metrics2.avg_complexity or 0
    )

    # Generate summary
    summary = _generate_comparison_summary(
        metrics1, metrics2,
        contrib_change, lang_change, fw_change, skill_change
    )

    return SnapshotComparison(
        snapshot1_name=project1.project_name,
        snapshot2_name=project2.project_name,
        summary=summary,
        contributors=MetricComparison(
            snapshot1_value=metrics1.contributor_count,
            snapshot2_value=metrics2.contributor_count,
            change=contrib_change,
            percent_change=contrib_percent,
        ),
        languages=MetricComparison(
            snapshot1_value=metrics1.languages,
            snapshot2_value=metrics2.languages,
            change=lang_change,
            percent_change=lang_percent,
        ),
        frameworks=MetricComparison(
            snapshot1_value=metrics1.frameworks,
            snapshot2_value=metrics2.frameworks,
            change=fw_change,
            percent_change=fw_percent,
        ),
        libraries=MetricComparison(
            snapshot1_value=metrics1.libraries,
            snapshot2_value=metrics2.libraries,
            change=lib_change,
            percent_change=lib_percent,
        ),
        skills=MetricComparison(
            snapshot1_value=metrics1.skill_count,
            snapshot2_value=metrics2.skill_count,
            change=skill_change,
            percent_change=skill_percent,
        ),
        total_files=MetricComparison(
            snapshot1_value=metrics1.total_files,
            snapshot2_value=metrics2.total_files,
            change=files_change,
            percent_change=files_percent,
        ),
        total_loc=MetricComparison(
            snapshot1_value=metrics1.total_loc,
            snapshot2_value=metrics2.total_loc,
            change=loc_change,
            percent_change=loc_percent,
        ),
        avg_complexity=MetricComparison(
            snapshot1_value=metrics1.avg_complexity,
            snapshot2_value=metrics2.avg_complexity,
            change=complexity_change,
            percent_change=complexity_percent,
        ),
        snapshot1_metrics=metrics1,
        snapshot2_metrics=metrics2,
        new_contributors=[],  # Would need detailed analysis data
        new_languages=new_languages,
        new_frameworks=new_frameworks,
        new_libraries=new_libraries,
    )


def _convert_to_snapshot_metrics(project) -> SnapshotMetrics:
    """Convert an AnalysisResult to SnapshotMetrics."""
    return SnapshotMetrics(
        snapshot_name=project.project_name,
        total_commits=0,  # Not stored directly in project, would need to count from contributors
        contributor_count=project.contributor_count,
        languages=project.languages,
        frameworks=project.frameworks,
        libraries=project.libraries,
        tools=project.tools_and_technologies,
        skill_count=project.skill_count,
        total_files=project.file_count,
        total_loc=project.total_lines_of_code,
        avg_complexity=project.complexity_summary.avg_complexity if project.complexity_summary else None,
        first_commit_date=str(project.first_commit_date) if project.first_commit_date else None,
    )


def _generate_comparison_summary(
    metrics1: SnapshotMetrics,
    metrics2: SnapshotMetrics,
    contrib_change: int,
    lang_change: int,
    fw_change: int,
    skill_change: int,
) -> str:
    """Generate a human-readable summary of the comparison."""
    summary_parts = []

    if contrib_change and contrib_change > 0:
        summary_parts.append(f"{contrib_change} new contributor(s)")
    elif contrib_change and contrib_change < 0:
        summary_parts.append(f"{abs(contrib_change)} fewer contributor(s)")

    if lang_change and lang_change > 0:
        summary_parts.append(f"{lang_change} new language(s)")

    if fw_change and fw_change > 0:
        summary_parts.append(f"{fw_change} new framework(s)")

    if skill_change and skill_change > 0:
        summary_parts.append(f"{skill_change} new skill(s)")

    if not summary_parts:
        return "No significant changes detected between snapshots"

    return "Changes: " + ", ".join(summary_parts)
