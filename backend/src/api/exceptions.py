"""Custom exception handlers for FastAPI."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class ProjectNotFoundError(HTTPException):
    """Exception raised when a project is not found."""

    def __init__(self, project_id: int):
        super().__init__(
            status_code=404,
            detail=f"Project with ID {project_id} not found",
        )


class AnalysisError(HTTPException):
    """Exception raised when analysis fails."""

    def __init__(self, message: str):
        super().__init__(
            status_code=500,
            detail=f"Analysis failed: {message}",
        )


class InvalidFileError(HTTPException):
    """Exception raised for invalid file uploads."""

    def __init__(self, message: str):
        super().__init__(
            status_code=400,
            detail=f"Invalid file: {message}",
        )


class InvalidGitHubURLError(HTTPException):
    """Exception raised for invalid GitHub URLs."""

    def __init__(self, url: str):
        super().__init__(
            status_code=400,
            detail=f"Invalid GitHub URL: {url}",
        )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Generic exception handler for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc),
        },
    )
