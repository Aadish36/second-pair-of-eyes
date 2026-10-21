"""Health endpoint."""

from fastapi import APIRouter

from schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def read_health() -> HealthResponse:
    """Provide a lightweight process liveness check."""
    return HealthResponse(status="ok", service="second-pair-of-eyes-api")
