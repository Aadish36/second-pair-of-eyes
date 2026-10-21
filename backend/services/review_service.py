"""Business logic for code review submissions."""

from datetime import datetime, timezone
from uuid import uuid4

from schemas.reviews import ReviewRequest, ReviewResult
from services.ai_review import enrich_review
from services import pylint_service, review_store


def create_review(request: ReviewRequest) -> ReviewResult:
    issues = pylint_service.analyze_python(request.code, request.filename)
    issues, ai_status, ai_message = enrich_review(request.code, issues)
    result = ReviewResult(
        id=str(uuid4()),
        status="completed",
        filename=request.filename,
        pull_request_number=request.pull_request_number,
        title=request.title,
        created_at=datetime.now(timezone.utc),
        issue_count=len(issues),
        issues=issues,
        ai_review_status=ai_status,
        ai_review_message=ai_message,
    )
    review_store.save_review(result)
    return result
