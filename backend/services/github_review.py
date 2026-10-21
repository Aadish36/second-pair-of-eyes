"""Pull request diff analysis, AI enrichment, and verified static review comments."""

from __future__ import annotations

import hashlib
from html import escape
import re
from datetime import datetime, timezone
from uuid import uuid4

from config import settings
from schemas.reviews import ReviewResult
from services import ai_review, database, pylint_service
from services.github_app import GitHubAppClient

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def added_lines_by_path(diff: str) -> dict[str, set[int]]:
    """Map each diff path to line numbers added on the new side of the patch."""
    result: dict[str, set[int]] = {}
    current_path: str | None = None
    new_line: int | None = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_path = line[6:]
            result.setdefault(current_path, set())
            new_line = None
            continue
        match = _HUNK.match(line)
        if match:
            new_line = int(match.group(1))
            result.setdefault(current_path or "", set())
            continue
        if new_line is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if current_path:
                result.setdefault(current_path, set()).add(new_line)
            new_line += 1
        elif line.startswith(" "):
            new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
    return result


def _comment(issue) -> dict:
    # Only deterministic analyzer output is posted. AI explanations and history
    # references are persisted for the dashboard/API but are not trusted as claims.
    body = (f"<p><strong>{escape(issue.severity.upper())} · {escape(issue.issue_type)}</strong></p>"
            f"<p>Static analyzer:</p><pre>{escape(issue.message)}</pre>"
            f"<p>Suggested next step: {escape(issue.suggested_next_step)}</p>")
    return {"path": issue.path, "line": issue.line_number, "side": "RIGHT", "body": body}


def process_pull_request(repository: str, number: int, installation_id: int,
                         client: GitHubAppClient | None = None,
                         expected_head_sha: str | None = None) -> dict:
    github = client or GitHubAppClient(installation_id, repository=repository)
    pr = github.get_pull_request(repository, number)
    head_sha = pr["head"]["sha"]
    if expected_head_sha and head_sha != expected_head_sha:
        return {"head_sha": head_sha, "stale": True, "issue_count": 0,
                "comment_count": 0, "github_review_id": None}
    title = pr.get("title") or f"Pull request #{number}"
    files = github.get_changed_files(repository, number)
    diff = github.get_pull_request_diff(repository, number)
    changed_lines = added_lines_by_path(diff)
    all_issues = []
    ai_statuses = []
    ai_messages = []

    for file in files:
        path = file.get("filename", "")
        if not path.lower().endswith(".py") or file.get("status") == "removed":
            continue
        try:
            source = github.get_file_at_ref(repository, path, head_sha)
        except Exception as exc:
            # A deleted/renamed-away file can disappear between the file-list and
            # contents calls. Other API errors should bubble up for webhook retry.
            if getattr(exc, "status_code", None) == 404:
                continue
            raise
        if not source.strip() or len(source) > settings.max_source_chars:
            continue
        issues = pylint_service.analyze_python(source, path)
        issues, ai_status, ai_message = ai_review.enrich_review(source, issues)
        ai_statuses.append(ai_status)
        if ai_message:
            ai_messages.append(ai_message)
        added = changed_lines.get(path, set())
        for issue in issues:
            if issue.line_number in added:
                all_issues.append(issue.model_copy(update={"path": path}))

    if github.get_pull_request(repository, number)["head"]["sha"] != head_sha:
        return {"head_sha": head_sha, "stale": True, "issue_count": len(all_issues),
                "comment_count": 0, "github_review_id": None}

    result = ReviewResult(
        id=str(uuid4()), status="completed", filename="<pull request>",
        pull_request_number=number, title=title, created_at=datetime.now(timezone.utc),
        issue_count=len(all_issues), issues=all_issues,
        ai_review_status=("unavailable" if "unavailable" in ai_statuses else
                          "disabled" if not ai_statuses or all(s == "disabled" for s in ai_statuses)
                          else "completed"),
        ai_review_message=("No changed Python source was eligible for analysis; AI enrichment did not run."
                           if not ai_statuses else
                           "AI enrichment ran per changed Python file. GitHub comments include static analyzer evidence only. "
                           + ("Agent note: " + "; ".join(ai_messages) if ai_messages else "")),
    )
    comments = [_comment(issue) for issue in all_issues if issue.path and issue.line_number][:50]
    posted_review = None
    if comments:
        marker = f"<!-- second-pair-of-eyes:{repository}:{number}:{head_sha} -->"
        existing = next((review for review in github.get_pull_request_reviews(repository, number)
                         if marker in (review.get("body") or "")), None)
        posted_review = existing or github.post_review(
            repository, number, head_sha,
            f"Second Pair of Eyes found {len(comments)} static analyzer finding(s) on changed lines. "
            "AI generated explanations and historical claims are not included in these comments.\n\n" + marker,
            comments,
        )
    persisted = {
        "review": result.model_dump(mode="json"),
        "changed_files": [file.get("filename") for file in files],
        "head_sha": head_sha,
        "diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
    }
    database.finish_pr_revision(repository, number, head_sha, title, persisted,
                                posted_review.get("id") if posted_review else None)
    return {"head_sha": head_sha, "stale": False, "issue_count": len(all_issues),
            "comment_count": len(comments), "github_review_id": posted_review.get("id") if posted_review else None}
