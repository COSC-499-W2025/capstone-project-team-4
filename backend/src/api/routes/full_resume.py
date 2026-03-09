"""Full resume generation and export API routes."""

import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from src.api.exceptions import UserNotFoundError
from src.models.database import get_db
from src.models.schemas.full_resume import FullResumeData
from src.services.full_resume_service import FullResumeService

# For auth
from src.models.orm.user import User
from src.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["full-resume"])


def _safe_filename(name: str) -> str:
    """Convert a name to a safe ASCII filename segment."""
    safe = re.sub(r"[^\w\s-]", "", name).strip()
    return re.sub(r"[\s]+", "_", safe) or "resume"


@router.get("/{user_id}/resume", response_model=FullResumeData)
async def get_resume_json(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compose and return a full structured resume as JSON.

    - Aggregates profile, education, experience, projects, and skills
    - Returns graceful fallbacks when sections are missing
    - 404 if the user does not exist
    """
    service = FullResumeService(db)
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        return service.compose_resume(user_id)
    except ValueError:
        raise UserNotFoundError(user_id)


@router.get("/{user_id}/resume/export")
async def export_resume(
    user_id: int,
    format: str = Query("pdf", description="Export format: pdf, html, or markdown"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export the full resume in the requested format.

    - **format=pdf** → `application/pdf`
    - **format=html** → `text/html`
    - **format=markdown** → `text/markdown`
    - 400 if format is invalid, 404 if user not found
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    valid_formats = {"pdf", "html", "markdown"}
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{format}'. Must be one of: {', '.join(sorted(valid_formats))}",
        )

    service = FullResumeService(db)
    try:
        data = service.compose_resume(user_id)
    except ValueError:
        raise UserNotFoundError(user_id)

    filename_base = _safe_filename(data.contact.name)

    if format == "pdf":
        pdf_bytes = service.export_pdf(data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="resume_{filename_base}.pdf"'
            },
        )

    if format == "html":
        html_str = service.export_html(data)
        return Response(
            content=html_str.encode("utf-8"),
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="resume_{filename_base}.html"'
            },
        )

    # markdown
    md_str = service.export_markdown(data)
    return Response(
        content=md_str.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="resume_{filename_base}.md"'
        },
    )
