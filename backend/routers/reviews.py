"""Code review submission and result endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from config import settings
from schemas.reviews import ReviewRequest, ReviewResult
from services.review_service import create_review
from services.review_store import get_review
from services.auth import require_dashboard_access

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResult, status_code=201, dependencies=[Depends(require_dashboard_access)])
async def submit_review(request: ReviewRequest) -> ReviewResult:
    """Analyze submitted Python source as text; the code is never executed."""
    if len(request.code) > settings.max_source_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Source exceeds the {settings.max_source_chars} character limit.",
        )
    try:
        return create_review(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{review_id}", response_model=ReviewResult, dependencies=[Depends(require_dashboard_access)])
async def read_review(review_id: str) -> ReviewResult:
    """Retrieve a completed review by its identifier."""
    review = get_review(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return review
