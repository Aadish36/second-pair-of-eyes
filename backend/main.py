"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.health import router as health_router
from routers.auth import router as auth_router
from routers.dashboard import router as dashboard_router
from routers.github_webhooks import router as github_webhooks_router
from routers.pull_requests import router as pull_requests_router
from routers.reviews import router as reviews_router

app = FastAPI(
    title="Second Pair of Eyes API",
    description=(
        "Review source statically, process authenticated GitHub pull request events, "
        "and browse persisted webhook review findings. Submitted code is analyzed "
        "as text and is never executed."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(pull_requests_router, prefix="/api")
app.include_router(github_webhooks_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


@app.get("/", tags=["status"])
async def read_root() -> dict[str, str]:
    """Return API identity and links to documentation and health."""
    return {
        "name": "Second Pair of Eyes API",
        "status": "running",
        "health": "/api/health",
        "docs": "/docs",
    }
