"""Debug endpoint to check project root path."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.repositories.project_repository import ProjectRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/project/{project_id}")
async def debug_project(project_id: int, db: Session = Depends(get_db)):
    """Debug endpoint to check project details."""
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project.id,
        "project_name": project.name,
        "root_path": project.root_path,
        "root_path_type": type(project.root_path).__name__,
        "root_path_len": len(str(project.root_path)) if project.root_path else 0,
    }


@router.get("/contributor/{contributor_id}")
async def debug_contributor(contributor_id: int, db: Session = Depends(get_db)):
    """Debug endpoint to check contributor details."""
    from src.repositories.contributor_repository import ContributorRepository

    contributor_repo = ContributorRepository(db)
    contributor = contributor_repo.get(contributor_id)

    if not contributor:
        raise HTTPException(status_code=404, detail="Contributor not found")

    files = contributor_repo.get_with_files(contributor_id)
    files_count = len(files.files_modified) if files and files.files_modified else 0

    return {
        "contributor_id": contributor.id,
        "name": contributor.name,
        "email": contributor.email,
        "project_id": contributor.project_id,
        "files_count": files_count,
    }
