"""Full resume generation and export API routes."""

import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.api.exceptions import UserNotFoundError
from src.models.database import get_db

# For auth
from src.models.orm.user import User
from src.models.schemas.full_resume import FullResumeData
from src.services.full_resume_service import FullResumeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["full-resume"])


_VALID_FORMATS = {"pdf", "html", "markdown"}


def _safe_filename(name: str) -> str:
    """Convert a name to a safe ASCII filename segment."""
    safe = re.sub(r"[^\w\s-]", "", name).strip()
    return re.sub(r"[\s]+", "_", safe) or "resume"


def _validate_format(format: str) -> None:
    if format not in _VALID_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{format}'. Must be one of: {', '.join(sorted(_VALID_FORMATS))}",
        )


def _build_export_response(service: FullResumeService, data: FullResumeData, format: str) -> Response:
    """Render FullResumeData to the requested format and return a download Response."""
    filename_base = _safe_filename(data.contact.name)

    if format == "pdf":
        return Response(
            content=service.export_pdf(data),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="resume_{filename_base}.pdf"'},
        )

    if format == "html":
        return Response(
            content=service.export_html(data).encode("utf-8"),
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="resume_{filename_base}.html"'},
        )

    return Response(
        content=service.export_markdown(data).encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="resume_{filename_base}.md"'},
    )


@router.post("/resume/export")
async def export_resume_from_data(
    data: FullResumeData,
    format: str = Query("pdf", description="Export format: pdf, html, or markdown"),
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export an arbitrary FullResumeData payload in the requested format.

    - Data is not persisted — used for live export from the Resume Builder form.
    - **format=pdf** → `application/pdf`
    - **format=html** → `text/html`
    - **format=markdown** → `text/markdown`
    """
    _validate_format(format)
    return _build_export_response(FullResumeService(db), data, format)


@router.get("/{user_id}/resume", response_model=FullResumeData)
async def get_resume_json(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compose and return a full structured resume as JSON.

    - Aggregates profile, education, experience, projects, and skills
    - Returns graceful fallbacks when sections are missing
    - 404 if the user does not exist
    """
    service = FullResumeService(db)
    try:
        data = service.compose_resume(user_id)
    except ValueError:
        raise UserNotFoundError(user_id)
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return data


@router.get("/{user_id}/resume/export")
async def export_resume(
    user_id: int,
    format: str = Query("pdf", description="Export format: pdf, html, or markdown"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export the full resume in the requested format.

    - **format=pdf** → `application/pdf`
    - **format=html** → `text/html`
    - **format=markdown** → `text/markdown`
    - 400 if format is invalid, 404 if user not found
    """
    _validate_format(format)
    service = FullResumeService(db)
    try:
        data = service.compose_resume(user_id)
    except ValueError:
        raise UserNotFoundError(user_id)
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return _build_export_response(service, data, format)
