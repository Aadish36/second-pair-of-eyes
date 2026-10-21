"""Environment-backed application settings."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    frontend_origins: list[str]
    max_source_chars: int
    ai_review_mode: str
    openai_api_key: str | None
    openai_model: str
    history_repo_path: str | None
    chroma_path: str
    history_max_commits: int
    database_url: str | None
    github_webhook_secret: str | None
    github_app_id: str | None
    github_app_private_key: str | None
    github_app_private_key_path: str | None
    github_api_url: str
    github_api_version: str
    github_request_timeout_seconds: int
    github_max_retries: int
    dashboard_api_token: str | None
    dashboard_cookie_secure: bool


def _positive_int(value: str | None, default: int) -> int:
    try:
        parsed = int(value) if value else default
    except ValueError:
        return default
    return parsed if parsed > 0 else default


settings = Settings(
    frontend_origins=[
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ],
    max_source_chars=_positive_int(os.getenv("MAX_SOURCE_CHARS"), 100_000),
    ai_review_mode=os.getenv("AI_REVIEW_MODE", "mock").strip().lower(),
    openai_api_key=os.getenv("OPENAI_API_KEY") or None,
    openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    history_repo_path=os.getenv("HISTORY_REPO_PATH") or None,
    chroma_path=os.getenv("CHROMA_PATH", ".data/chroma"),
    history_max_commits=_positive_int(os.getenv("HISTORY_MAX_COMMITS"), 500),
    database_url=os.getenv("DATABASE_URL") or None,
    github_webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET") or None,
    github_app_id=os.getenv("GITHUB_APP_ID") or None,
    github_app_private_key=os.getenv("GITHUB_APP_PRIVATE_KEY") or None,
    github_app_private_key_path=os.getenv("GITHUB_APP_PRIVATE_KEY_PATH") or None,
    github_api_url=os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/"),
    github_api_version=os.getenv("GITHUB_API_VERSION", "2026-03-10"),
    github_request_timeout_seconds=_positive_int(os.getenv("GITHUB_REQUEST_TIMEOUT_SECONDS"), 20),
    github_max_retries=_positive_int(os.getenv("GITHUB_MAX_RETRIES"), 3),
    dashboard_api_token=os.getenv("DASHBOARD_API_TOKEN") or None,
    dashboard_cookie_secure=os.getenv("DASHBOARD_COOKIE_SECURE", "false").strip().lower() == "true",
)
