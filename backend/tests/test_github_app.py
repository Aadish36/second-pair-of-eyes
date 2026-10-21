"""GitHub API retrieval, retry, and comment posting tests with an HTTP mock transport."""

import httpx
from types import SimpleNamespace

from services.github_app import GitHubAppClient


def test_fetches_pull_request_files_diff_content_and_posts_review(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/pulls/7/files"):
            return httpx.Response(200, json=[{"filename": "src/app.py", "patch": "@@ -1 +1 @@"}])
        if request.url.path.endswith("/pulls/7/reviews") and request.method == "GET":
            return httpx.Response(200, json=[])
        if request.headers.get("accept") == "application/vnd.github.diff":
            return httpx.Response(200, text="diff --git a/src/app.py b/src/app.py")
        if "/contents/" in request.url.path:
            return httpx.Response(200, text="print('ok')")
        return httpx.Response(200, json={"number": 7})

    monkeypatch.setattr("services.github_app.settings", SimpleNamespace(
        github_api_url="https://api.github.test", github_api_version="2022-11-28",
        github_request_timeout_seconds=3, github_max_retries=1))
    client = GitHubAppClient(123, transport=httpx.MockTransport(handler))
    client._token = "test-installation-token"

    assert client.get_pull_request("owner/repo", 7)["number"] == 7
    assert client.get_changed_files("owner/repo", 7)[0]["filename"] == "src/app.py"
    assert "diff --git" in client.get_pull_request_diff("owner/repo", 7)
    assert client.get_file_at_ref("owner/repo", "src/app.py", "abc") == "print('ok')"


def test_posts_inline_review_comments_to_the_requested_pr(monkeypatch):
    captured = []

    def handler(request):
        captured.append(request)
        return httpx.Response(200, json={"id": 99})

    monkeypatch.setattr("services.github_app.settings", SimpleNamespace(
        github_api_url="https://api.github.test", github_api_version="2026-03-10",
        github_request_timeout_seconds=3, github_max_retries=1))
    client = GitHubAppClient(123, transport=httpx.MockTransport(handler))
    client._token = "test-installation-token"
    comments = [{"path": "src/app.py", "line": 9, "side": "RIGHT", "body": "Static finding"}]
    result = client.post_review("owner/repo", 7, "abc", "Summary", comments)
    assert result["id"] == 99
    assert captured[0].method == "POST"
    assert captured[0].url.path == "/repos/owner/repo/pulls/7/reviews"
    assert captured[0].headers["authorization"] == "Bearer test-installation-token"
    assert captured[0].read()  # JSON request body is present.


def test_retries_rate_limited_api_call(monkeypatch):
    attempts = []

    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, text="slow down")
        return httpx.Response(200, json={"number": 7})

    monkeypatch.setattr("services.github_app.settings", SimpleNamespace(
        github_api_url="https://api.github.test", github_api_version="2022-11-28",
        github_request_timeout_seconds=3, github_max_retries=1))
    monkeypatch.setattr("services.github_app.time.sleep", lambda _: None)
    client = GitHubAppClient(123, transport=httpx.MockTransport(handler))
    client._token = "test-token"
    assert client.get_pull_request("owner/repo", 7)["number"] == 7
    assert len(attempts) == 2
