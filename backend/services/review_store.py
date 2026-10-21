"""Process-local storage for review results during the starter stage."""

from schemas.reviews import ReviewResult

_reviews: dict[str, ReviewResult] = {}


def save_review(review: ReviewResult) -> None:
    _reviews[review.id] = review


def get_review(review_id: str) -> ReviewResult | None:
    return _reviews.get(review_id)


def list_reviews() -> list[ReviewResult]:
    return sorted(_reviews.values(), key=lambda item: item.created_at, reverse=True)


def clear_reviews() -> None:
    """Clear process-local reviews; primarily used by isolated tests."""
    _reviews.clear()
