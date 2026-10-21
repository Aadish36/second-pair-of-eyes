"""Authenticated GitHub webhook ingestion."""

import hashlib
import hmac
import json
import re

from fastapi import APIRouter, HTTPException, Request

from config import settings
from services import database
from services.github_app import GitHubAPIError
from services.github_review import process_pull_request

router = APIRouter(prefix="/webhooks", tags=["github"])
MAX_WEBHOOK_BYTES = 2_000_000
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def valid_signature(body: bytes, signature: str | None, secret: str | None = None) -> bool:
    key = secret or settings.github_webhook_secret
    if not key or not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(key.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/github")
async def github_webhook(request: Request) -> dict[str, str | int | None]:
    if not settings.github_webhook_secret:
        raise HTTPException(status_code=503, detail="GitHub webhook integration is not configured.")
    try:
        content_length = int(request.headers.get("content-length", "0") or 0)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid Content-Length header.") from exc
    if content_length > MAX_WEBHOOK_BYTES:
        raise HTTPException(status_code=413, detail="Webhook payload is too large.")
    body = await request.body()
    if len(body) > MAX_WEBHOOK_BYTES:
        raise HTTPException(status_code=413, detail="Webhook payload is too large.")
    if not valid_signature(body, request.headers.get("x-hub-signature-256")):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature.")

    event = request.headers.get("x-github-event", "")
    delivery_id = request.headers.get("x-github-delivery", "")
    if not delivery_id or len(delivery_id) > 128 or not event:
        raise HTTPException(status_code=400, detail="GitHub event and delivery headers are required.")
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Webhook body must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payload must be a JSON object.")

    if event != "pull_request" or payload.get("action") not in {"opened", "synchronize"}:
        return {"status": "ignored", "delivery_id": delivery_id}

    pr = payload.get("pull_request") or {}
    repository_data = payload.get("repository") or {}
    installation_data = payload.get("installation") or {}
    if not all(isinstance(item, dict) for item in (pr, repository_data, installation_data)):
        raise HTTPException(status_code=400, detail="Webhook metadata has an invalid shape.")
    head_data = pr.get("head") or {}
    if not isinstance(head_data, dict):
        raise HTTPException(status_code=400, detail="Webhook pull request head has an invalid shape.")
    repository = repository_data.get("full_name", "")
    installation_id = installation_data.get("id")
    number = payload.get("number")
    if (not _REPOSITORY.fullmatch(repository) or type(number) is not int or number < 1
            or type(installation_id) is not int or installation_id < 1
            or not head_data.get("sha")):
        raise HTTPException(status_code=400, detail="Webhook is missing repository, installation, pull request, or head metadata.")
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL is required for webhook processing.")

    try:
        database.initialize_database()
        delivery_claim = database.claim_delivery(delivery_id, event)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Webhook persistence is unavailable; retry this delivery.") from exc
    if delivery_claim == "duplicate":
        return {"status": "duplicate", "delivery_id": delivery_id}
    if delivery_claim == "in_progress":
        return {"status": "in_progress", "delivery_id": delivery_id}

    try:
        claimed = database.claim_pr_revision(repository, number, pr.get("head", {}).get("sha", ""), pr.get("title") or "")
        if not claimed:
            database.update_delivery(delivery_id, "completed")
            return {"status": "already_reviewed", "delivery_id": delivery_id}
        expected_head_sha = pr.get("head", {}).get("sha", "")
        summary = process_pull_request(repository, number, installation_id, expected_head_sha=expected_head_sha)
        if summary.get("stale"):
            database.finish_pr_revision(repository, number, expected_head_sha, pr.get("title") or "",
                {"status": "stale_event", "observed_head_sha": summary["head_sha"]}, None)
            database.update_delivery(delivery_id, "completed")
            return {"status": "stale_event", "delivery_id": delivery_id}
        database.update_delivery(delivery_id, "completed")
        return {"status": "completed", "delivery_id": delivery_id, **summary}
    except Exception as exc:
        try:
            database.fail_pr_revision(repository, number, pr.get("head", {}).get("sha", ""), str(exc))
            database.update_delivery(delivery_id, "failed", str(exc))
        except Exception:
            pass
        status = 503
        if isinstance(exc, GitHubAPIError) and not exc.retryable:
            status = 422
        raise HTTPException(status_code=status, detail="Pull request review failed; this delivery can be retried.") from exc
