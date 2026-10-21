"""Persistence idempotency tests using SQLite; production uses PostgreSQL."""

from services import database


def test_webhook_and_pull_request_claims_are_idempotent(tmp_path):
    database.configure_database(f"sqlite:///{tmp_path / 'webhooks.db'}")
    database.initialize_database()
    assert database.claim_delivery("delivery-1", "pull_request") == "claimed"
    assert database.claim_delivery("delivery-1", "pull_request") == "in_progress"
    database.update_delivery("delivery-1", "failed", "temporary failure")
    assert database.claim_delivery("delivery-1", "pull_request") == "claimed"
    database.update_delivery("delivery-1", "completed")
    assert database.claim_delivery("delivery-1", "pull_request") == "duplicate"

    assert database.claim_pr_revision("owner/repo", 7, "abc", "title")
    assert not database.claim_pr_revision("owner/repo", 7, "abc", "title")
    assert database.claim_pr_revision("owner/repo", 7, "def", "title")
