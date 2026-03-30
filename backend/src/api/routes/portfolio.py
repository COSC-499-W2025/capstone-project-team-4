"""Portfolio API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.orm.user import User
from src.models.schemas.portfolio import (
    PortfolioResponse,
    PortfolioProjectCustomize,
    PortfolioUpdate,
)
from src.api.exceptions import PortfolioNotFoundError
from src.services.portfolio_service import PortfolioService
from src.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.post("/generate", response_model=PortfolioResponse, status_code=201)
async def generate_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a portfolio for the authenticated user.

    - Requires authentication (Bearer token)
    - Aggregates all project data, skills, resume items, profile, and experiences
    - Uses AI to generate a portfolio summary (falls back to template if unavailable)
    - Creates or updates the user's portfolio
    - Returns 201 with the created/updated portfolio
    """
    service = PortfolioService(db)
    try:
        result = service.generate_portfolio(current_user)
    except Exception as e:
        logger.error(f"Portfolio generation failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio generation failed: {str(e)}",
        )
    return result


@router.put(
    "/{portfolio_id}/projects/{project_name}/customize",
    response_model=PortfolioResponse,
)
def customize_portfolio_project(
    portfolio_id: int,
    project_name: str,
    update_data: PortfolioProjectCustomize,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add custom names, descriptions, or URLs to a generated portfolio project.
    """
    service = PortfolioService(db)

    result, error = service.customize_project(
        portfolio_id=portfolio_id,
        user_id=current_user.id,
        project_name=project_name,
        update_data=update_data,
    )

    if error:
        if error == "Not authorized to edit this portfolio":
            raise HTTPException(status_code=403, detail=error)
        raise HTTPException(status_code=404, detail=error)

    return result


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a portfolio by ID.

    - Public endpoint (no authentication required)
    - Returns 200 with the portfolio data
    - Returns 404 if portfolio not found
    """
    service = PortfolioService(db)
    result = service.get_portfolio(portfolio_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return result


@router.put("/{portfolio_id}/edit", response_model=PortfolioResponse)
async def edit_portfolio(
    portfolio_id: int,
    data: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Edit an existing portfolio.

    - Requires authentication (Bearer token)
    - Only the portfolio owner can edit it
    - Supports partial updates (only provided fields are changed)
    - Returns 200 with the updated portfolio
    """
    service = PortfolioService(db)
    result = service.update_portfolio(portfolio_id, data, current_user)

    if result is None:
        raise PortfolioNotFoundError(current_user.id)

    if result == "forbidden":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to edit this portfolio",
        )

    return result
