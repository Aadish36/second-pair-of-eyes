"""Database-backed dashboard summary and learning trend endpoints."""

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from config import settings
from services import database
from services.auth import require_dashboard_access

router = APIRouter(prefix="/dashboard", tags=["dashboard"],
                    dependencies=[Depends(require_dashboard_access)])


def _category(issue: dict) -> str:
    text = f"{issue.get('issue_type', '')} {issue.get('message', '')}".lower()
    if any(word in text for word in ("security", "injection", "password", "secret", "bandit")):
        return "Security"
    if any(word in text for word in ("performance", "complexity", "slow", "inefficient")):
        return "Performance"
    if any(word in text for word in ("style", "naming", "documentation", "maintainability")):
        return "Maintainability"
    return "Reliability"


def _dashboard_items(records) -> list[dict]:
    items = []
    for record in records:
        stored = record.result or {}
        review = stored.get("review", {})
        if not isinstance(review, dict) or not review:
            continue
        issues = review.get("issues", [])
        if not isinstance(issues, list):
            issues = []
        items.append({
            "id": review.get("id", f"{record.repository}#{record.pull_number}@{record.head_sha}"),
            "number": record.pull_number,
            "title": record.title,
            "repository": record.repository,
            "head_sha": record.head_sha,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "status": record.status,
            "issue_count": len(issues),
            "issues": issues,
            "ai_review_status": review.get("ai_review_status", "unavailable"),
            "ai_review_message": review.get("ai_review_message"),
            "changed_files": stored.get("changed_files", []),
            "github_review_id": record.github_review_id,
            "github_url": f"https://github.com/{record.repository}/pull/{record.pull_number}",
        })
    return items


@router.get("/summary")
async def dashboard_summary() -> dict:
    """Summarize persisted GitHub PR reviews; never fabricate absent activity."""
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL is required for persisted dashboard data.")
    try:
        database.initialize_database()
        items = _dashboard_items(database.list_completed_pr_reviews())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Dashboard database is unavailable.") from exc

    findings = [issue for item in items for issue in item["issues"]]
    category_counts = Counter(_category(issue) for issue in findings)
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=55)
    weeks = []
    for offset in range(8):
        week_start = start + timedelta(days=offset * 7)
        week_end = week_start + timedelta(days=7)
        bucket = {"week": week_start.strftime("%b %d"), "security": 0, "reliability": 0,
                  "maintainability": 0, "performance": 0}
        for item in items:
            created = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).date()
            if week_start <= created < week_end:
                for issue in item["issues"]:
                    bucket[_category(issue).lower()] += 1
        weeks.append(bucket)
    return {
        "items": items,
        "total": len(items),
        "metrics": {
            "pull_requests_reviewed": len(items),
            "issues_found": len(findings),
            "critical_issues": sum(issue.get("severity") == "critical" for issue in findings),
            "resolved_issues": None,
        },
        "categories": [{"label": key, "count": category_counts.get(key, 0)}
                       for key in ("Reliability", "Security", "Maintainability", "Performance")],
        "trends": weeks,
        "source": "postgresql",
    }
