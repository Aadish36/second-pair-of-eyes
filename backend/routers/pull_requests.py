"""Pull request summaries derived from submitted reviews."""

from fastapi import APIRouter, Depends, HTTPException

from schemas.pull_requests import PullRequestItem, PullRequestList
from schemas.reviews import ReviewIssue
from services.review_store import list_reviews
from config import settings
from services import database
from services.auth import require_dashboard_access

router = APIRouter(prefix="/pull-requests", tags=["pull requests"])


@router.get("", response_model=PullRequestList, dependencies=[Depends(require_dashboard_access)])
async def read_pull_requests() -> PullRequestList:
    """List persisted webhook reviews and process-local manual review submissions."""
    items: list[PullRequestItem] = []
    if settings.database_url:
        try:
            database.initialize_database()
            for record in database.list_completed_pr_reviews():
                review_data = (record.result or {}).get("review", {})
                if not review_data:
                    continue
                issues_data = review_data.get("issues", [])
                issues = [ReviewIssue.model_validate(issue) for issue in issues_data]
                severity_order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
                items.append(PullRequestItem(
                    number=record.pull_number, title=record.title, filename="<pull request>",
                    review_id=review_data.get("id", f"{record.repository}#{record.pull_number}@{record.head_sha}"),
                    created_at=record.updated_at, issue_count=len(issues),
                    highest_severity=max((i.severity for i in issues), key=lambda s: severity_order[s], default="info"),
                    issues=issues,
                ))
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Pull request database is unavailable.") from exc
    for review in list_reviews():
        if review.pull_request_number is None:
            continue
        severity_order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        highest = max(
            (issue.severity for issue in review.issues),
            key=lambda severity: severity_order.get(severity, 0),
            default="info",
        )
        items.append(
            PullRequestItem(
                number=review.pull_request_number,
                title=review.title or f"Pull request #{review.pull_request_number}",
                filename=review.filename,
                review_id=review.id,
                created_at=review.created_at,
                issue_count=review.issue_count,
                highest_severity=highest,
                issues=review.issues,
            )
        )
    return PullRequestList(items=items, total=len(items))
