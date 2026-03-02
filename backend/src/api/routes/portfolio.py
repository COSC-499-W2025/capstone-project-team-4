"""Portfolio API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.orm.user import User
from src.models.schemas.portfolio import PortfolioResponse
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
