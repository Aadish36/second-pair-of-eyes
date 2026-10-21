"""Request and response models for code reviews."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, description="Python source code to lint; never executed.")
    filename: str = Field(default="submitted.py", min_length=1, max_length=255)
    pull_request_number: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, max_length=300)

    @field_validator("code")
    @classmethod
    def code_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Code must contain non-whitespace source text.")
        return value

    @field_validator("filename")
    @classmethod
    def filename_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Filename must not be blank.")
        return value


class HistoricalExample(BaseModel):
    commit_sha: str
    short_sha: str
    subject: str
    evidence: str
    url: str | None = None


class ReviewIssue(BaseModel):
    path: str | None = None
    issue_type: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    line_number: int | None
    message: str
    suggested_next_step: str
    explanation: str | None = None
    risk: str | None = None
    fix_guidance: str | None = None
    historical_examples: list[HistoricalExample] = Field(default_factory=list)
    history_message: str = "No relevant historical example was found."


class ReviewResult(BaseModel):
    id: str
    status: Literal["completed"]
    filename: str
    pull_request_number: int | None
    title: str | None
    created_at: datetime
    issue_count: int
    issues: list[ReviewIssue]
    ai_review_status: Literal["completed", "unavailable", "disabled"] = "completed"
    ai_review_message: str | None = None
