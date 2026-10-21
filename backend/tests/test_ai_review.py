"""Unit tests for agent output validation and graceful fallback behavior."""

import subprocess
from types import SimpleNamespace

from schemas.reviews import ReviewIssue
from services import ai_review


def _issue():
    return ReviewIssue(
        issue_type="undefined-variable",
        severity="high",
        line_number=2,
        message="Undefined variable 'missing_name'",
        suggested_next_step="Define the name before use.",
    )


def test_mock_mode_returns_teaching_explanation_and_no_history(monkeypatch):
    monkeypatch.setattr(ai_review, "settings", SimpleNamespace(ai_review_mode="mock", history_repo_path=None))

    issues, status, message = ai_review.enrich_review("print(missing_name)", [_issue()])

    assert status == "completed"
    assert message and "not configured" in message
    assert "undefined variable" in issues[0].explanation.lower()
    assert issues[0].risk
    assert issues[0].fix_guidance == "Define the name before use."
    assert issues[0].historical_examples == []
    assert issues[0].history_message == ai_review.NO_HISTORY


def test_live_mode_without_key_falls_back_to_static_issue(monkeypatch):
    monkeypatch.setattr(ai_review, "settings", SimpleNamespace(ai_review_mode="live", openai_api_key=None, history_repo_path=None))

    issues, status, message = ai_review.enrich_review("print(missing_name)", [_issue()])

    assert status == "unavailable"
    assert "OPENAI_API_KEY" in message
    assert issues[0].message == "Undefined variable 'missing_name'"
    assert issues[0].explanation is None


def test_off_mode_skips_agent_graph(monkeypatch):
    monkeypatch.setattr(ai_review, "settings", SimpleNamespace(ai_review_mode="off"))

    issues, status, message = ai_review.enrich_review("x", [_issue()])

    assert status == "disabled"
    assert "disabled" in message
    assert issues[0].historical_examples == []


def test_verifier_accepts_only_existing_commit_patch_evidence(monkeypatch, tmp_path):
    sha = "a" * 40
    patch_text = "diff --git a/fix.py b/fix.py\n+return None\n"
    monkeypatch.setattr(
        ai_review,
        "settings",
        SimpleNamespace(history_repo_path=str(tmp_path)),
    )

    def fake_git(repo, *args):
        if args[0] == "cat-file":
            if args[-1].startswith("b"):
                raise subprocess.CalledProcessError(1, ["git", *args])
            return ""
        if args[0:3] == ("show", "-s", "--format=%s"):
            return "Fix missing return value\n"
        if args[0] == "show":
            return patch_text
        raise AssertionError(args)

    monkeypatch.setattr(ai_review, "_git", fake_git)
    state = {
        "issues": [_issue()],
        "retrieved": [[
            {"sha": sha, "subject": "Fix missing return value", "evidence": "Fix missing return value\n" + patch_text},
            {"sha": "b" * 40, "subject": "Unsupported claim", "evidence": "text not in patch"},
            {"sha": sha, "subject": "Fix missing return value", "evidence": "text not in patch"},
        ]],
    }

    verified = ai_review._verify(state)["verified"]

    assert len(verified[0]) == 1
    assert verified[0][0].commit_sha == sha
    assert verified[0][0].subject == "Fix missing return value"
