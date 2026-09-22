import httpx
import pytest

from core.config import settings


async def _get(path, headers=None):
    from app.main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        return await c.get(path, headers=headers)


async def test_health_is_public(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "k")
    assert (await _get("/health")).status_code == 200


@pytest.mark.parametrize("path", ["/students", "/leads", "/partners/1"])
async def test_protected_routes_reject_missing_and_wrong_key(monkeypatch, path):
    monkeypatch.setattr(settings, "admin_api_key", "k")
    assert (await _get(path)).status_code == 401
    assert (await _get(path, {"X-Admin-Key": "wrong"})).status_code == 401


async def test_fails_closed_when_key_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "")
    assert (await _get("/students", {"X-Admin-Key": ""})).status_code == 503
