import os

import httpx
import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="needs TEST_DATABASE_URL")

STAGING = "https://api.edubao.lifeinurl.com"
PK = "p_abc"


@pytest.fixture
async def client():
    from app.deps import init_edubao
    from app.main import app
    from core.config import settings
    from db.session import engine

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE partner_accounts, edubao_call_log RESTART IDENTITY CASCADE"))
    settings.admin_api_key = "test-admin"
    init_edubao(app)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://t", headers={"X-Admin-Key": "test-admin"}
    ) as c:
        yield c
    await app.state.edubao_http.aclose()
    await engine.dispose()


def mock_edubao(respx):
    respx.post(f"{STAGING}/api/v1/user/signin").respond(
        json={"data": {"access_token": "login", "partner_key": PK, "user_key": PK}, "status": True}
    )
    respx.post(f"{STAGING}/api/v1/partners/{PK}/initiate-cred-otp").respond(json={"status": True})
    respx.post(f"{STAGING}/api/v1/partners/{PK}/verify-cred-otp").respond(
        json={"user_key": PK, "x_api_key": "pk_secret", "client_id": "cid", "client_secret": "csec"}
    )
    respx.post(f"{STAGING}/api/v1/partners/{PK}/access-token").respond(
        json={"access_token": "oauth-tok", "refresh_token": "ref", "expires_in": 7200, "status": True}
    )


async def test_full_onboarding_stores_everything_encrypted(client, respx_mock):
    from sqlalchemy import select

    from core.security import decrypt
    from db.models import PartnerAccount
    from db.session import SessionLocal

    mock_edubao(respx_mock)
    body = {"name": "Acme", "environment": "staging", "login_email": "a@b.co", "password": "hunter2"}

    r = await client.post("/partners/onboard/start", json=body)
    assert r.status_code == 201 and r.json()["onboarded"] is False
    assert "hunter2" not in r.text and "password" not in r.json()
    acct_id = r.json()["id"]

    r = await client.post(f"/partners/onboard/{acct_id}/verify-otp", json={"otp": "123456"})
    assert r.status_code == 200 and r.json()["onboarded"] is True
    assert r.json()["access_token_expires_at"] is not None
    for secret in ("hunter2", "pk_secret", "csec", "oauth-tok"):
        assert secret not in r.text

    async with SessionLocal() as s:
        acct = (await s.execute(select(PartnerAccount))).scalar_one()
        assert acct.password_enc != "hunter2" and decrypt(acct.password_enc) == "hunter2"
        assert decrypt(acct.x_api_key_enc) == "pk_secret" and decrypt(acct.access_token_enc) == "oauth-tok"
        logs = (await s.execute(text("select request_summary::text from edubao_call_log"))).scalars().all()
        assert logs and not any(x in " ".join(logs) for x in ("hunter2", "csec"))


async def test_bad_login_maps_to_400(client, respx_mock):
    respx_mock.post(f"{STAGING}/api/v1/user/signin").respond(401, json={"message": "Invalid credentials"})
    r = await client.post(
        "/partners/onboard/start",
        json={"name": "x", "login_email": "a@b.co", "password": "bad"},
    )
    assert r.status_code == 400 and "Invalid credentials" in r.json()["detail"]


async def test_verify_unknown_account_404(client):
    r = await client.post("/partners/onboard/999/verify-otp", json={"otp": "1"})
    assert r.status_code == 404
