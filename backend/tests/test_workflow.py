"""Mocked end-to-end GitHub delivery through persistence and dashboard reads."""

import hashlib
import hmac
import json
from types import SimpleNamespace

import pytest

from routers import dashboard, github_webhooks
from services import ai_review, auth, database, github_review
from schemas.reviews import ReviewIssue


@pytest.fixture(autouse=True)
def clear_database_override():
    database._session_factory_override(None)
    yield
    database._session_factory_override(None)


class FakeGitHub:
    last_posted = None

    def __init__(self, *args, **kwargs):
        self.posted = None

    def get_pull_request(self, repository, number):
        return {"title": "Fix missing name", "head": {"sha": "a" * 40}}

    def get_changed_files(self, repository, number):
        return [{"filename": "app.py", "status": "modified"}]

    def get_pull_request_diff(self, repository, number):
        return "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n old\n+return missing\n"

    def get_file_at_ref(self, repository, path, sha):
        return "def run():\n    return missing\n"

    def get_pull_request_reviews(self, repository, number):
        return []

    def post_review(self, repository, number, commit_id, body, comments):
        self.posted = {"body": body, "comments": comments}
        type(self).last_posted = self.posted
        return {"id": 321}


def test_signed_pr_delivery_to_agent_review_comment_postgres_and_dashboard(client, tmp_path, monkeypatch):
    database.configure_database(f"sqlite:///{tmp_path / 'workflow.db'}")
    monkeypatch.setattr(github_webhooks, "settings", SimpleNamespace(
        github_webhook_secret="test-secret", database_url="sqlite:///workflow.db"))
    monkeypatch.setattr(dashboard, "settings", SimpleNamespace(database_url="sqlite:///workflow.db"))
    monkeypatch.setattr(auth, "settings", SimpleNamespace(dashboard_api_token=None))
    monkeypatch.setattr(github_review, "settings", SimpleNamespace(max_source_chars=10_000))
    monkeypatch.setattr(ai_review, "settings", SimpleNamespace(
        ai_review_mode="mock", history_repo_path=None, history_max_commits=10))
    monkeypatch.setattr(github_review, "GitHubAppClient", FakeGitHub)
    monkeypatch.setattr(github_review.pylint_service, "analyze_python", lambda source, filename: [
        ReviewIssue(issue_type="undefined-variable", severity="high", line_number=2,
                    message="Undefined variable 'missing'", suggested_next_step="Define the name.")
    ])

    payload = {
        "action": "opened", "number": 7,
        "repository": {"full_name": "example/app"},
        "installation": {"id": 123},
        "pull_request": {"title": "Fix missing name", "head": {"sha": "a" * 40}},
    }
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
    response = client.post("/api/webhooks/github", content=body, headers={
        "x-hub-signature-256": signature,
        "x-github-event": "pull_request",
        "x-github-delivery": "workflow-delivery-1",
    })

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "completed"
    record = database.list_completed_pr_reviews()[0]
    finding = record.result["review"]["issues"][0]
    assert finding["explanation"]
    assert finding["risk"]
    assert finding["historical_examples"] == []
    assert record.github_review_id == 321
    comment_body = FakeGitHub.last_posted["comments"][0]["body"]
    assert "Static analyzer" in comment_body
    assert "behave differently" not in comment_body

    summary = client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["items"][0]["issue_count"] == 1
    assert summary.json()["items"][0]["issues"][0]["explanation"] == finding["explanation"]

    repeated = client.post("/api/webhooks/github", content=body, headers={
        "x-hub-signature-256": signature,
        "x-github-event": "pull_request",
        "x-github-delivery": "workflow-delivery-2",
    })
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "already_reviewed"
