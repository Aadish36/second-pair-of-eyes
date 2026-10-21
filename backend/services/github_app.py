"""Minimal GitHub App authentication and API client with bounded retries."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import httpx
import jwt

from config import settings


class GitHubAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


def _private_key() -> str:
    if settings.github_app_private_key:
        return settings.github_app_private_key.replace("\\n", "\n")
    if settings.github_app_private_key_path:
        return Path(settings.github_app_private_key_path).expanduser().read_text(encoding="utf-8")
    raise RuntimeError("Configure GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH.")


def app_jwt(now: datetime | None = None) -> str:
    if not settings.github_app_id:
        raise RuntimeError("GITHUB_APP_ID is required for GitHub App authentication.")
    issued = now or datetime.now(timezone.utc)
    return jwt.encode({"iat": int(issued.timestamp()) - 60,
                       "exp": int((issued + timedelta(minutes=9)).timestamp()),
                       "iss": settings.github_app_id}, _private_key(), algorithm="RS256")


class GitHubAppClient:
    def __init__(self, installation_id: int, transport: httpx.BaseTransport | None = None,
                 repository: str | None = None):
        self.installation_id = installation_id
        self.transport = transport
        self.repository = repository
        self._token: str | None = None

    def _http(self) -> httpx.Client:
        return httpx.Client(timeout=settings.github_request_timeout_seconds, transport=self.transport)

    def _installation_token(self) -> str:
        if self._token:
            return self._token
        token_scope = None
        if self.repository:
            token_scope = {"repositories": [self.repository.split("/", 1)[1]],
                           "permissions": {"contents": "read", "pull_requests": "write"}}
        response = self._request("POST", "/app/installations/{}/access_tokens".format(self.installation_id),
                                 token=app_jwt(), app_auth=True, json_body=token_scope)
        self._token = response.json()["token"]
        return self._token

    def _request(self, method: str, path: str, *, token: str | None = None, app_auth: bool = False,
                 params: dict | None = None, json_body: dict | None = None, accept: str | None = None) -> httpx.Response:
        headers = {"Accept": accept or "application/vnd.github+json",
                   "User-Agent": "Second-Pair-of-Eyes",
                   "X-GitHub-Api-Version": settings.github_api_version}
        auth = token
        if not app_auth:
            auth = auth or self._installation_token()
        headers["Authorization"] = f"Bearer {auth}"
        max_attempts = settings.github_max_retries + 1
        for attempt in range(max_attempts):
            try:
                with self._http() as client:
                    response = client.request(method, settings.github_api_url + path, headers=headers,
                                              params=params, json=json_body)
            except httpx.RequestError as exc:
                if attempt + 1 >= max_attempts:
                    raise GitHubAPIError(503, f"GitHub network request failed: {type(exc).__name__}", True) from exc
                time.sleep(min(2 ** attempt, 8))
                continue
            response_text = response.text[:500]
            rate_limit_body = any(term in response_text.lower() for term in
                                  ("secondary rate limit", "rate limit exceeded", "abuse detection"))
            rate_limited = response.status_code == 429 or (response.status_code == 403 and (
                response.headers.get("Retry-After") or response.headers.get("X-RateLimit-Remaining") == "0" or rate_limit_body
            ))
            retryable = response.status_code in {500, 502, 503, 504} or bool(rate_limited)
            if retryable and attempt + 1 < max_attempts:
                delay = response.headers.get("Retry-After")
                try:
                    if delay:
                        wait = float(delay)
                    elif response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                        reset_at = float(response.headers.get("X-RateLimit-Reset", "0"))
                        wait = max(0, reset_at - time.time())
                    elif rate_limit_body:
                        raise GitHubAPIError(response.status_code,
                                             "GitHub secondary rate limit requires delayed redelivery.", True)
                    else:
                        wait = min(2 ** attempt, 8)
                except ValueError:
                    wait = min(2 ** attempt, 8)
                if wait > 10:
                    raise GitHubAPIError(response.status_code,
                                         "GitHub rate limit requires delayed redelivery.", True)
                time.sleep(max(wait, 0))
                continue
            if response.is_error:
                message = response_text
                raise GitHubAPIError(response.status_code, f"GitHub API returned {response.status_code}: {message}", retryable)
            return response
        raise GitHubAPIError(503, "GitHub API retries exhausted.", True)

    def get_pull_request(self, repository: str, number: int) -> dict:
        return self._request("GET", f"/repos/{repository}/pulls/{number}").json()

    def get_pull_request_diff(self, repository: str, number: int) -> str:
        return self._request("GET", f"/repos/{repository}/pulls/{number}",
                             accept="application/vnd.github.diff").text

    def get_changed_files(self, repository: str, number: int) -> list[dict]:
        files: list[dict] = []
        for page in range(1, 4):  # GitHub's PR files endpoint caps results at 300 files.
            batch = self._request("GET", f"/repos/{repository}/pulls/{number}/files",
                                  params={"per_page": 100, "page": page}).json()
            files.extend(batch)
            if len(batch) < 100:
                break
        return files

    def get_pull_request_reviews(self, repository: str, number: int) -> list[dict]:
        reviews: list[dict] = []
        for page in range(1, 11):
            batch = self._request("GET", f"/repos/{repository}/pulls/{number}/reviews",
                                  params={"per_page": 100, "page": page}).json()
            reviews.extend(batch)
            if len(batch) < 100:
                break
        return reviews

    def get_file_at_ref(self, repository: str, path: str, ref: str) -> str:
        encoded = quote(path, safe="/")
        return self._request("GET", f"/repos/{repository}/contents/{encoded}", params={"ref": ref},
                             accept="application/vnd.github.raw+json").text

    def post_review(self, repository: str, number: int, commit_id: str, body: str,
                    comments: list[dict]) -> dict:
        return self._request("POST", f"/repos/{repository}/pulls/{number}/reviews",
                             json_body={"commit_id": commit_id, "body": body, "event": "COMMENT", "comments": comments}).json()
