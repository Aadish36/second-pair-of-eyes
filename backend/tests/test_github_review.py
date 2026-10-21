"""Review generation and safe inline comment construction without external services."""

from types import SimpleNamespace

from schemas.reviews import ReviewIssue
from services import github_review


class FakeGitHub:
    def __init__(self):
        self.posted = None

    def get_pull_request(self, repository, number):
        return {"title": "Update app", "head": {"sha": "a" * 40}}

    def get_changed_files(self, repository, number):
        return [{"filename": "app.py", "status": "modified"}, {"filename": "notes.md", "status": "modified"}]

    def get_pull_request_diff(self, repository, number):
        return "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n old\n+return missing\n"

    def get_file_at_ref(self, repository, path, sha):
        return "def run():\n    return missing\n"

    def get_pull_request_reviews(self, repository, number):
        return getattr(self, "existing_reviews", [])

    def post_review(self, repository, number, commit_id, body, comments):
        self.posted = {"repository": repository, "number": number, "commit_id": commit_id, "body": body, "comments": comments}
        return {"id": 88}


def test_diff_mapping_and_review_pipeline_only_posts_changed_static_findings(monkeypatch):
    fake = FakeGitHub()
    calls = {"ai": 0, "persisted": None}
    issue = ReviewIssue(issue_type="undefined-variable", severity="high", line_number=2,
                        message="Undefined variable 'missing'", suggested_next_step="Define this name.",
                        explanation="Unverified model explanation", risk="Unverified model risk",
                        historical_examples=[{"commit_sha": "bad", "short_sha": "bad", "subject": "invented", "evidence": "invented"}])
    monkeypatch.setattr(github_review, "settings", SimpleNamespace(max_source_chars=1000, ai_review_mode="mock"))
    monkeypatch.setattr(github_review.pylint_service, "analyze_python", lambda source, path: [issue])

    def enrich(source, issues):
        calls["ai"] += 1
        return issues, "completed", None

    monkeypatch.setattr(github_review.ai_review, "enrich_review", enrich)
    monkeypatch.setattr(github_review.database, "finish_pr_revision",
                        lambda *args: calls.__setitem__("persisted", args))

    result = github_review.process_pull_request("owner/repo", 7, 123, client=fake)

    assert github_review.added_lines_by_path(fake.get_pull_request_diff("owner/repo", 7))["app.py"] == {2}
    assert calls["ai"] == 1
    assert result["comment_count"] == 1
    assert result["github_review_id"] == 88
    assert "Static analyzer: Undefined variable 'missing'" in fake.posted["comments"][0]["body"]
    assert "Unverified" not in fake.posted["comments"][0]["body"]
    assert "invented" not in fake.posted["comments"][0]["body"]
    assert fake.posted["comments"][0]["line"] == 2
    assert calls["persisted"][-1] == 88


def test_no_added_line_findings_do_not_post_empty_review(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(github_review, "settings", SimpleNamespace(max_source_chars=1000, ai_review_mode="off"))
    monkeypatch.setattr(github_review.pylint_service, "analyze_python", lambda source, path: [
        ReviewIssue(issue_type="x", severity="low", line_number=1, message="old line", suggested_next_step="Review")
    ])
    monkeypatch.setattr(github_review.ai_review, "enrich_review", lambda source, issues: (issues, "disabled", None))
    monkeypatch.setattr(github_review.database, "finish_pr_revision", lambda *args: None)
    result = github_review.process_pull_request("owner/repo", 7, 123, client=fake)
    assert result["comment_count"] == 0
    assert fake.posted is None


def test_existing_review_marker_prevents_duplicate_comment_post(monkeypatch):
    fake = FakeGitHub()
    fake.existing_reviews = [{"id": 88, "body": f"<!-- second-pair-of-eyes:owner/repo:7:{'a' * 40} -->"}]
    monkeypatch.setattr(github_review, "settings", SimpleNamespace(max_source_chars=1000, ai_review_mode="mock"))
    monkeypatch.setattr(github_review.pylint_service, "analyze_python", lambda source, path: [
        ReviewIssue(issue_type="x", severity="low", line_number=2, message="finding", suggested_next_step="Review")
    ])
    monkeypatch.setattr(github_review.ai_review, "enrich_review", lambda source, issues: (issues, "completed", None))
    monkeypatch.setattr(github_review.database, "finish_pr_revision", lambda *args: None)
    result = github_review.process_pull_request("owner/repo", 7, 123, client=fake)
    assert result["github_review_id"] == 88
    assert fake.posted is None
