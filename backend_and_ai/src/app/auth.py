import secrets

from fastapi import Header, HTTPException

from core.config import settings


async def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """Guard for every non-public route. Fails closed if ADMIN_API_KEY is unset."""
    expected = settings.admin_api_key
    if not expected:
        raise HTTPException(503, "ADMIN_API_KEY is not configured")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(401, "Invalid or missing X-Admin-Key")
