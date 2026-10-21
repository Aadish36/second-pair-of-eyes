"""Dashboard persistence and access-control checks using SQLite."""

from types import SimpleNamespace

import pytest

from routers import dashboard
from services import auth, database


@pytest.fixture(autouse=True)
def clear_database_override():
    database._session_factory_override(None)
    yield
    database._session_factory_override(None)


def test_dashboard_summary_uses_persisted_findings(client, tmp_path, monkeypatch):
    database.configure_database(f"sqlite:///{tmp_path / 'dashboard.db'}")
    database.initialize_database()
    assert database.claim_pr_revision("example/app", 12, "abc123", "Fix input validation")
    database.finish_pr_revision(
        "example/app", 12, "abc123", "Fix input validation",
        {"review": {"id": "r1", "issues": [
            {"issue_type": "undefined-variable", "severity": "high", "message": "Undefined name"},
            {"issue_type": "security-injection", "severity": "critical", "message": "Possible injection"},
        ], "ai_review_status": "completed"}, "changed_files": ["app.py"]},
        101,
    )
    monkeypatch.setattr(dashboard, "settings", SimpleNamespace(database_url="sqlite://"))
    monkeypatch.setattr(auth, "settings", SimpleNamespace(dashboard_api_token=None))

    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["source"] == "postgresql"
    assert data["total"] == 1
    assert data["metrics"]["issues_found"] == 2
    assert data["metrics"]["critical_issues"] == 1
    assert {item["label"]: item["count"] for item in data["categories"]}["Security"] == 1
    assert data["items"][0]["github_review_id"] == 101


def test_dashboard_requires_token_and_accepts_http_only_session(client, monkeypatch):
    monkeypatch.setattr(auth, "settings", SimpleNamespace(dashboard_api_token="demo-token"))
    monkeypatch.setattr(dashboard.database, "initialize_database", lambda: (_ for _ in ()).throw(RuntimeError("db down")))
    denied = client.get("/api/dashboard/summary")
    assert denied.status_code == 401

    login = client.post("/api/auth/login", json={"token": "demo-token"})
    assert login.status_code == 200
    assert "httponly" in login.headers["set-cookie"].lower()
    status = client.get("/api/dashboard/summary")
    assert status.status_code == 503  # Auth passed; PostgreSQL is not configured in this test.


def test_dashboard_login_rejects_bad_token(client, monkeypatch):
    monkeypatch.setattr(auth, "settings", SimpleNamespace(dashboard_api_token="expected"))
    response = client.post("/api/auth/login", json={"token": "wrong"})
    assert response.status_code == 401
