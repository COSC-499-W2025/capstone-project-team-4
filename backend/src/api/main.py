"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.models.database import init_db

from src.api.routes import (
    analysis,
    projects,
    skills,
    resume,
    user_profiles,
    auth,
    privacy_settings,
    experience,
    snapshots,
    contributor_analysis,
    contributors,
    debug,
    full_resume,
    portfolio,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Project Analyzer API")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Project Analyzer API")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Project Analyzer API - Analyze GitHub repositories and project files to extract
    insights about programming languages, frameworks, code complexity, and generate
    professional resume-worthy bullet points.

    ## Features

    * **Project Analysis** - Analyze projects from ZIP uploads or GitHub URLs
    * **Language Detection** - Detect programming languages and frameworks
    * **Code Complexity** - Calculate cyclomatic complexity metrics
    * **Skill Extraction** - Extract technical skills from code patterns
    * **Resume Generation** - Generate professional resume bullet points
    * **User Profiles** - Manage user personal information and experiences
    * **Authentication** - User registration and login
    * **Privacy Settings** - Manage AI consent preferences

    ## API Endpoints

    * `/api/auth/register` - Register new user
    * `/api/auth/login` - Authenticate user
    * `/api/projects/analyze/upload` - Upload ZIP file for analysis
    * `/api/projects/analyze/github` - Analyze GitHub repository
    * `/api/projects` - List and manage analyzed projects
    * `/api/projects/{id}/skills` - Get extracted skills
    * `/api/projects/{id}/complexity` - Get complexity metrics
    * `/api/projects/{id}/resume` - Get/regenerate resume items
    * `/api/user-profiles` - Manage user profiles and experiences
    * `/api/privacy-settings` - Manage AI consent settings
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(analysis.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(snapshots.router, prefix=settings.api_prefix)
app.include_router(skills.router, prefix=settings.api_prefix)
app.include_router(resume.router, prefix=settings.api_prefix)
app.include_router(user_profiles.router, prefix=settings.api_prefix)
app.include_router(contributor_analysis.router, prefix=settings.api_prefix)
app.include_router(contributors.router, prefix=settings.api_prefix)
app.include_router(experience.router, prefix=settings.api_prefix)
app.include_router(privacy_settings.router, prefix=settings.api_prefix)
app.include_router(portfolio.router, prefix=settings.api_prefix)
app.include_router(debug.router)
app.include_router(full_resume.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
