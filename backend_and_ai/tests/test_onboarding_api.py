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
        json={"user_key": PK, "x_api_key": "pk_secret", "oauth_client": {"client_id": "cid", "client_secret": "csec"}}
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


async def test_signin_without_partner_access_maps_to_clean_502(client, respx_mock):
    """A real Edubao account that isn't Partner-API-enabled yet omits access_token/partner_key
    instead of erroring — this must not surface as a raw pydantic crash."""
    respx_mock.post(f"{STAGING}/api/v1/user/signin").respond(
        json={"data": {"id": 184, "user_type": "Partner", "email_id": "a@b.co"}, "status": True}
    )
    r = await client.post(
        "/partners/onboard/start",
        json={"name": "x", "login_email": "a@b.co", "password": "pw"},
    )
    assert r.status_code == 502
    assert "Edubao:" in r.json()["detail"] and "access_token" in r.json()["detail"]


async def test_verify_unknown_account_404(client):
    r = await client.post("/partners/onboard/999/verify-otp", json={"otp": "1"})
    assert r.status_code == 404


async def test_list_partners_returns_onboarded_accounts(client, respx_mock):
    mock_edubao(respx_mock)
    body = {"name": "Acme", "environment": "staging", "login_email": "a@b.co", "password": "hunter2"}
    started = await client.post("/partners/onboard/start", json=body)
    acct_id = started.json()["id"]

    r = await client.get("/partners")
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()]
    assert acct_id in ids
    assert "hunter2" not in r.text


async def _onboarded(client, respx_mock) -> int:
    mock_edubao(respx_mock)
    body = {"name": "Acme", "environment": "staging", "login_email": "a@b.co", "password": "pw"}
    acct_id = (await client.post("/partners/onboard/start", json=body)).json()["id"]
    await client.post(f"/partners/onboard/{acct_id}/verify-otp", json={"otp": "123456"})
    return acct_id


async def test_edubao_lead_lookup(client, respx_mock):
    acct_id = await _onboarded(client, respx_mock)
    route = respx_mock.post(f"{STAGING}/api/v1/partners/{PK}/get-lead").respond(
        json={"status": True, "data": {"lead": {"lead_id": 1880, "account_id": "CX-01-BA-1235"}}}
    )
    r = await client.get(f"/partners/{acct_id}/edubao-lead", params={"edubao_account_id": "CX-01-BA-1235"})
    assert r.status_code == 200 and r.json()["lead_id"] == 1880
    assert b"CX-01-BA-1235" in route.calls[0].request.content


async def test_edubao_lead_not_found_maps_to_404(client, respx_mock):
    acct_id = await _onboarded(client, respx_mock)
    respx_mock.post(f"{STAGING}/api/v1/partners/{PK}/get-lead").respond(
        400, json={"status": False, "message": "Lead not found."}
    )
    r = await client.get(f"/partners/{acct_id}/edubao-lead", params={"lead_id": 9})
    assert r.status_code == 404


async def test_edubao_lead_requires_an_id(client, respx_mock):
    acct_id = await _onboarded(client, respx_mock)
    assert (await client.get(f"/partners/{acct_id}/edubao-lead")).status_code == 422


async def test_edubao_rate_limit_maps_to_429_with_retry_after(client, respx_mock):
    acct_id = await _onboarded(client, respx_mock)
    respx_mock.post(f"{STAGING}/api/v1/partners/{PK}/get-lead").respond(
        429, headers={"RateLimit-Reset": "60"}, json={"status": 429, "error": "Too many requests, please try again later."}
    )
    r = await client.get(f"/partners/{acct_id}/edubao-lead", params={"lead_id": 1})
    assert r.status_code == 429 and r.headers["retry-after"] == "60"


async def test_token_failure_keeps_credentials_and_retry_succeeds(client, respx_mock):
    mock_edubao(respx_mock)
    token_url = f"{STAGING}/api/v1/partners/{PK}/access-token"
    token = respx_mock.post(token_url)
    token.side_effect = [
        httpx.Response(400, json={"status": False, "message": "Invalid client credentials"}),
        httpx.Response(200, json={"access_token": "oauth-tok", "refresh_token": "ref", "expires_in": 7200, "status": True}),
    ]
    body = {"name": "Acme", "environment": "staging", "login_email": "a@b.co", "password": "hunter2"}
    acct_id = (await client.post("/partners/onboard/start", json=body)).json()["id"]

    r = await client.post(f"/partners/onboard/{acct_id}/verify-otp", json={"otp": "123456"})
    assert r.status_code == 400 and "Invalid client credentials" in r.json()["detail"]
    assert (await client.get(f"/partners/{acct_id}")).json()["onboarded"] is True  # creds survived

    r = await client.post(f"/partners/onboard/{acct_id}/retry-token")
    assert r.status_code == 200 and r.json()["access_token_expires_at"] is not None
    sent = token.calls[1].request.content
    assert b"client_id=cid" in sent and b"client_secret=csec" in sent and b"user_password=hunter2" in sent


async def test_retry_token_without_credentials_404(client, respx_mock):
    mock_edubao(respx_mock)
    body = {"name": "Acme", "environment": "staging", "login_email": "a@b.co", "password": "pw"}
    acct_id = (await client.post("/partners/onboard/start", json=body)).json()["id"]
    assert (await client.post(f"/partners/onboard/{acct_id}/retry-token")).status_code == 404
