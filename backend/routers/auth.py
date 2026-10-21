"""Shared-token login for local/private dashboard access."""

import hmac

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1, max_length=512)


@router.get("/status")
async def auth_status() -> dict[str, bool]:
    return {"authentication_required": settings.dashboard_api_token is not None}


@router.post("/login")
async def login(payload: LoginRequest, response: Response) -> dict[str, str]:
    expected = settings.dashboard_api_token
    if expected is None:
        return {"status": "authentication_disabled"}
    if not hmac.compare_digest(payload.token, expected):
        raise HTTPException(status_code=401, detail="Invalid dashboard token.")
    response.set_cookie("dashboard_session", expected, httponly=True, secure=settings.dashboard_cookie_secure,
                        samesite="strict", max_age=8 * 60 * 60, path="/")
    return {"status": "authenticated"}


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie("dashboard_session", path="/", httponly=True, samesite="strict")
    return {"status": "logged_out"}
