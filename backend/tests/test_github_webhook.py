"""Webhook signature, routing, and delivery idempotency tests; no GitHub is contacted."""

import hashlib  
import hmac
import json
from types import SimpleNamespace

from routers import github_webhooks


def _signed_headers(body, delivery="delivery-1", event="pull_request", secret="test-secret"):
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return {"x-hub-signature-256": signature, "x-github-event": event, "x-github-delivery": delivery}


def _payload(action="opened"):
    return {
        "action": action,
        "number": 7,
        "repository": {"full_name": "example/sandbox"},
        "installation": {"id": 123},
        "pull_request": {"title": "Test change", "head": {"sha": "a" * 40}},
    }


def test_signature_rejects_missing_or_tampered_signature():
    body = b'{"action":"opened"}'
    assert github_webhooks.valid_signature(body, _signed_headers(body)["x-hub-signature-256"], "test-secret")
    assert not github_webhooks.valid_signature(body, "sha256=bad", "test-secret")
    assert not github_webhooks.valid_signature(body, None, "test-secret")


def test_webhook_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setattr(github_webhooks, "settings", SimpleNamespace(github_webhook_secret="test-secret"))
    response = client.post("/api/webhooks/github", content=b"{}", headers={
        "x-hub-signature-256": "sha256=bad", "x-github-event": "pull_request", "x-github-delivery": "d1",
    })
    assert response.status_code == 401


def test_webhook_routes_authenticated_delivery_and_deduplicates(client, monkeypatch):
    monkeypatch.setattr(github_webhooks, "settings", SimpleNamespace(
        github_webhook_secret="test-secret", database_url="postgresql://test"))
    monkeypatch.setattr(github_webhooks.database, "initialize_database", lambda: None)
    states = {}

    def claim_delivery(delivery_id, event):
        if states.get(delivery_id) == "completed":
            return "duplicate"
        states[delivery_id] = "processing"
        return "claimed"

    monkeypatch.setattr(github_webhooks.database, "claim_delivery", claim_delivery)
    monkeypatch.setattr(github_webhooks.database, "claim_pr_revision", lambda *args: True)
    monkeypatch.setattr(github_webhooks, "process_pull_request", lambda *args, **kwargs: {"head_sha": "a" * 40, "stale": False, "issue_count": 1, "comment_count": 1, "github_review_id": 55})
    monkeypatch.setattr(github_webhooks.database, "update_delivery", lambda delivery_id, status, error=None: states.__setitem__(delivery_id, status))

    body = json.dumps(_payload()).encode()
    headers = _signed_headers(body)
    response = client.post("/api/webhooks/github", content=body, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    repeated = client.post("/api/webhooks/github", content=body, headers=headers)
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "duplicate"


def test_webhook_ignores_unhandled_action_after_signature_check(client, monkeypatch):
    monkeypatch.setattr(github_webhooks, "settings", SimpleNamespace(github_webhook_secret="test-secret"))
    body = json.dumps(_payload("closed")).encode()
    response = client.post("/api/webhooks/github", content=body, headers=_signed_headers(body))
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
