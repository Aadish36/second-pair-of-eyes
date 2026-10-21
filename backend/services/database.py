"""PostgreSQL persistence for webhook deliveries and pull request reviews."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import JSON

from config import settings


class Base(DeclarativeBase):
    pass


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    delivery_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="processing")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    error: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PullRequestReviewRecord(Base):
    __tablename__ = "pull_request_reviews"
    __table_args__ = (UniqueConstraint("repository", "pull_number", "head_sha", name="uq_pr_review_revision"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository: Mapped[str] = mapped_column(String(255), nullable=False)
    pull_number: Mapped[int] = mapped_column(Integer, nullable=False)
    head_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="processing")
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    github_review_id: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@lru_cache(maxsize=1)
def _session_factory() -> sessionmaker[Session]:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required for GitHub webhook processing.")
    engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    return sessionmaker(bind=engine, expire_on_commit=False)


def configure_database(url: str) -> None:
    """Configure an isolated engine; primarily useful for tests and local tooling."""
    factory = sessionmaker(bind=create_engine(url, pool_pre_ping=True, future=True), expire_on_commit=False)
    _session_factory_override(factory)


_test_factory: sessionmaker[Session] | None = None


def _session_factory_override(factory: sessionmaker[Session] | None) -> None:
    global _test_factory
    _test_factory = factory


def _sessions() -> sessionmaker[Session]:
    return _test_factory or _session_factory()


def initialize_database() -> None:
    Base.metadata.create_all(_sessions().kw["bind"])


def _recent(updated_at: datetime, now: datetime, lease_minutes: int) -> bool:
    if updated_at.tzinfo is None:  # SQLite test databases return naive timestamps.
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    return updated_at > now - timedelta(minutes=lease_minutes)


def claim_delivery(delivery_id: str, event: str, lease_minutes: int = 15) -> str:
    """Return claimed, duplicate, or in_progress; failed/stale deliveries can retry."""
    now = datetime.now(timezone.utc)
    with _sessions().begin() as session:
        record = session.get(WebhookDelivery, delivery_id, with_for_update=True)
        if record is None:
            session.add(WebhookDelivery(delivery_id=delivery_id, event=event, status="processing", attempts=1,
                                        received_at=now, updated_at=now))
            return "claimed"
        if record.status == "completed":
            return "duplicate"
        if record.status == "processing" and _recent(record.updated_at, now, lease_minutes):
            return "in_progress"
        record.status = "processing"
        record.event = event
        record.attempts += 1
        record.error = None
        record.updated_at = now
        return "claimed"


def update_delivery(delivery_id: str, status: str, error: str | None = None) -> None:
    with _sessions().begin() as session:
        record = session.get(WebhookDelivery, delivery_id, with_for_update=True)
        if record:
            record.status = status
            record.error = error[:2000] if error else None
            record.updated_at = datetime.now(timezone.utc)


def claim_pr_revision(repository: str, number: int, head_sha: str, title: str, lease_minutes: int = 15) -> bool:
    now = datetime.now(timezone.utc)
    with _sessions().begin() as session:
        record = session.scalar(select(PullRequestReviewRecord).where(
            PullRequestReviewRecord.repository == repository,
            PullRequestReviewRecord.pull_number == number,
            PullRequestReviewRecord.head_sha == head_sha,
        ).with_for_update())
        if record is None:
            session.add(PullRequestReviewRecord(repository=repository, pull_number=number, head_sha=head_sha,
                title=title[:500], status="processing", created_at=now, updated_at=now))
            return True
        if record.status == "completed" or (record.status == "processing" and _recent(record.updated_at, now, lease_minutes)):
            return False
        record.status = "processing"
        record.title = title[:500]
        record.error = None
        record.updated_at = now
        return True


def finish_pr_revision(repository: str, number: int, head_sha: str, title: str, result: dict[str, Any],
                       github_review_id: int | None) -> None:
    now = datetime.now(timezone.utc)
    with _sessions().begin() as session:
        record = session.scalar(select(PullRequestReviewRecord).where(
            PullRequestReviewRecord.repository == repository,
            PullRequestReviewRecord.pull_number == number,
            PullRequestReviewRecord.head_sha == head_sha,
        ).with_for_update())
        if record is None:
            raise RuntimeError("Pull request review claim disappeared before completion.")
        record.title = title[:500]
        record.status = "completed"
        record.result = result
        record.github_review_id = github_review_id
        record.error = None
        record.updated_at = now


def fail_pr_revision(repository: str, number: int, head_sha: str, error: str) -> None:
    with _sessions().begin() as session:
        record = session.scalar(select(PullRequestReviewRecord).where(
            PullRequestReviewRecord.repository == repository,
            PullRequestReviewRecord.pull_number == number,
            PullRequestReviewRecord.head_sha == head_sha,
        ).with_for_update())
        if record:
            record.status = "failed"
            record.error = error[:2000]
            record.updated_at = datetime.now(timezone.utc)


def list_completed_pr_reviews() -> list[PullRequestReviewRecord]:
    """Return persisted completed PR reviews, newest first, for read APIs."""
    with _sessions()() as session:
        return list(session.scalars(
            select(PullRequestReviewRecord)
            .where(PullRequestReviewRecord.status == "completed")
            .order_by(PullRequestReviewRecord.updated_at.desc())
        ).all())
