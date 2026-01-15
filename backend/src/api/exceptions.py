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


class UserProfileNotFoundError(HTTPException):
    """Exception raised when a user profile is not found."""

    def __init__(self, profile_id: int):
        super().__init__(
            status_code=404,
            detail=f"User profile with ID {profile_id} not found",
        )


class UserProfileEmailExistsError(HTTPException):
    """Exception raised when email already exists."""

    def __init__(self, email: str):
        super().__init__(
            status_code=409,
            detail=f"User profile with email {email} already exists",
        )


class WorkExperienceNotFoundError(HTTPException):
    """Exception raised when a work experience is not found."""

    def __init__(self, experience_id: int):
        super().__init__(
            status_code=404,
            detail=f"Work experience with ID {experience_id} not found",
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
