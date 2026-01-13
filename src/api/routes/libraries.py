"""Libraries API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.library import (
    ProjectLibrariesResponse,
    LibrarySummary,
)
from src.repositories.project_repository import ProjectRepository
from src.repositories.library_repository import LibraryRepository
from src.api.exceptions import ProjectNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/libraries", tags=["libraries"])


@router.get("", response_model=ProjectLibrariesResponse)
async def get_project_libraries(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all libraries detected in a project.

    - Returns libraries grouped by ecosystem (npm, pip, cargo, etc.)
    - Includes version and dev dependency information
    """
    project_repo = ProjectRepository(db)
    library_repo = LibraryRepository(db)

    project = project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # Get all libraries for the project
    project_libraries = library_repo.get_by_project(project_id)

    # Build library summaries
    libraries = []
    by_ecosystem = {}
    dev_count = 0
    prod_count = 0

    for proj_lib in project_libraries:
        lib_summary = LibrarySummary(
            name=proj_lib.library.name,
            ecosystem=proj_lib.library.ecosystem,
            version=proj_lib.version,
            is_dev_dependency=proj_lib.is_dev_dependency,
        )
        libraries.append(lib_summary)

        # Group by ecosystem
        ecosystem = proj_lib.library.ecosystem
        if ecosystem not in by_ecosystem:
            by_ecosystem[ecosystem] = []
        by_ecosystem[ecosystem].append(lib_summary)

        # Count dev vs prod
        if proj_lib.is_dev_dependency:
            dev_count += 1
        else:
            prod_count += 1

    # Get ecosystem counts
    ecosystem_counts = library_repo.count_by_ecosystem(project_id)

    return ProjectLibrariesResponse(
        project_id=project_id,
        project_name=project.name,
        libraries=libraries,
        by_ecosystem=by_ecosystem,
        ecosystem_counts=ecosystem_counts,
        total_count=len(libraries),
        dev_dependency_count=dev_count,
        production_dependency_count=prod_count,
    )


@router.get("/ecosystem/{ecosystem}")
async def get_libraries_by_ecosystem(
    project_id: int,
    ecosystem: str,
    db: Session = Depends(get_db),
):
    """
    Get libraries filtered by ecosystem.

    - Supported ecosystems: npm, pip, pyproject, poetry, cargo, go, maven, gradle, gem, composer, nuget, pub
    """
    project_repo = ProjectRepository(db)
    library_repo = LibraryRepository(db)

    project = project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    project_libraries = library_repo.get_by_ecosystem(project_id, ecosystem)

    libraries = []
    for proj_lib in project_libraries:
        libraries.append(LibrarySummary(
            name=proj_lib.library.name,
            ecosystem=proj_lib.library.ecosystem,
            version=proj_lib.version,
            is_dev_dependency=proj_lib.is_dev_dependency,
        ))

    return {
        "project_id": project_id,
        "ecosystem": ecosystem,
        "libraries": libraries,
        "count": len(libraries),
    }


@router.get("/ecosystems")
async def get_library_ecosystems(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all ecosystems detected in a project.

    - Returns list of unique ecosystem names
    """
    project_repo = ProjectRepository(db)
    library_repo = LibraryRepository(db)

    project = project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    ecosystems = library_repo.get_ecosystems(project_id)
    counts = library_repo.count_by_ecosystem(project_id)

    return {
        "project_id": project_id,
        "ecosystems": ecosystems,
        "counts": counts,
    }
