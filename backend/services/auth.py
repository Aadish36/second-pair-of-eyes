"""Optional bearer-token protection for dashboard read APIs."""

import hmac

from fastapi import Cookie, Header, HTTPException

from config import settings


def require_dashboard_access(authorization: str | None = Header(default=None),
                            dashboard_session: str | None = Cookie(default=None)) -> None:
    """Require a configured shared dashboard token; local mode is open by default."""
    expected = settings.dashboard_api_token
    if expected is None:
        return
    scheme, _, token = (authorization or "").partition(" ")
    if not ((scheme.lower() == "bearer" and token and hmac.compare_digest(token, expected))
            or (dashboard_session and hmac.compare_digest(dashboard_session, expected))):
        raise HTTPException(status_code=401, detail="Valid dashboard bearer token required.",
                            headers={"WWW-Authenticate": "Bearer"})
