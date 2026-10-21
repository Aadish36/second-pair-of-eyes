"""Pull request listing response models."""

from datetime import datetime

from pydantic import BaseModel

from schemas.reviews import ReviewIssue


class PullRequestItem(BaseModel):
    number: int
    title: str
    filename: str
    review_id: str
    created_at: datetime
    issue_count: int
    highest_severity: str
    issues: list[ReviewIssue]


class PullRequestList(BaseModel):
    items: list[PullRequestItem]
    total: int
