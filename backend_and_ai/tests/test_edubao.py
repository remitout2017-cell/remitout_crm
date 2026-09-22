from datetime import datetime, timedelta, timezone

import httpx
import pytest
import respx

from partners.edubao.auth import PartnerCredentials, TokenManager
from partners.edubao.client import EdubaoPartnerClient
from partners.edubao.errors import EdubaoAPIError, EdubaoAuthError, EdubaoTransportError
from partners.edubao.http import EdubaoHTTP
from partners.edubao.onboarding import EdubaoAuthAPI
from partners.edubao.recording import sanitize

BASE = "https://edubao.test"
PK = "p_abc"


class FakeStore:
    def __init__(self, token="tok1", expires_in=3600):
        self.creds = PartnerCredentials(
            account_id=1, base_url=BASE, login_email="a@b.c", partner_key=PK, x_api_key="key",
            client_id="cid", client_secret="sec", access_token=token,
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        )
        self.saves = 0

    async def load(self, account_id):
        return self.creds

    async def save_tokens(self, account_id, access_token, refresh_token, expires_at):
        self.creds.access_token, self.creds.refresh_token = access_token, refresh_token
        self.creds.access_token_expires_at = expires_at
        self.saves += 1


async def pw(_creds):
    return "secret-pw"


def build(store, password_provider=pw, recorder=None):
    http = EdubaoHTTP(recorder=recorder)
    tokens = TokenManager(store, EdubaoAuthAPI(http), password_provider)
    return EdubaoPartnerClient(1, http, store, tokens), http


TOKEN_URL = f"{BASE}/api/v1/partners/{PK}/access-token"
STEP_URL = f"{BASE}/api/v1/partners/{PK}/submit-blocked-account"


@respx.mock
async def test_sends_both_auth_headers_and_parses_step():
    route = respx.post(STEP_URL).respond(json={"id": 1880, "account_id": "CX-1", "status": True})
    client, _ = build(FakeStore())
    res = await client.submit_blocked_account(1, {"first_name": "John"})
    assert res.id == 1880 and res.account_id == "CX-1"
    req = route.calls[0].request
    assert req.headers["x-api-key"] == "key" and req.headers["authorization"] == "Bearer tok1"
    assert b'"step":1' in req.content.replace(b" ", b"")


@respx.mock
async def test_expired_token_is_renewed_before_call():
    store = FakeStore(expires_in=10)  # inside 60s leeway
    tok = respx.post(TOKEN_URL).respond(json={"access_token": "tok2", "expires_in": 7200, "status": True})
    respx.post(STEP_URL).respond(json={"id": 1, "status": True})
    client, _ = build(store)
    await client.submit_blocked_account(1, {})
    assert tok.call_count == 1 and store.creds.access_token == "tok2" and store.saves == 1


@respx.mock
async def test_401_triggers_single_refresh_and_retry():
    store = FakeStore()
    respx.post(TOKEN_URL).respond(json={"access_token": "tok2", "expires_in": 7200, "status": True})
    step = respx.post(STEP_URL).mock(
        side_effect=[httpx.Response(401, json={"message": "expired"}), httpx.Response(200, json={"id": 2, "status": True})]
    )
    client, _ = build(store)
    res = await client.submit_blocked_account(2, {})
    assert res.id == 2 and step.call_count == 2
    assert step.calls[1].request.headers["authorization"] == "Bearer tok2"


@respx.mock
async def test_persistent_401_raises():
    respx.post(TOKEN_URL).respond(json={"access_token": "tok2", "expires_in": 7200, "status": True})
    respx.post(STEP_URL).respond(401, json={"message": "nope"})
    client, _ = build(FakeStore())
    with pytest.raises(EdubaoAuthError):
        await client.submit_blocked_account(1, {})


@respx.mock
async def test_expired_without_password_raises_auth_error():
    client, _ = build(FakeStore(expires_in=-5), password_provider=None)
    with pytest.raises(EdubaoAuthError):
        await client.submit_blocked_account(1, {})


@respx.mock
async def test_concurrent_calls_share_one_refresh():
    import asyncio

    store = FakeStore(expires_in=-5)
    tok = respx.post(TOKEN_URL).respond(json={"access_token": "tok2", "expires_in": 7200, "status": True})
    respx.post(STEP_URL).respond(json={"id": 1, "status": True})
    client, _ = build(store)
    await asyncio.gather(*(client.submit_blocked_account(1, {}) for _ in range(5)))
    assert tok.call_count == 1


@respx.mock
async def test_retries_502_then_succeeds(monkeypatch):
    monkeypatch.setattr("asyncio.sleep", lambda *_: _noop())
    route = respx.post(STEP_URL).mock(
        side_effect=[httpx.Response(502), httpx.Response(200, json={"id": 3, "status": True})]
    )
    client, _ = build(FakeStore())
    assert (await client.submit_blocked_account(1, {})).id == 3
    assert route.call_count == 2


async def _noop():
    return None


@respx.mock
async def test_400_not_retried_and_message_surfaced():
    route = respx.post(STEP_URL).respond(400, json={"message": "invalid passport", "status": False})
    client, _ = build(FakeStore())
    with pytest.raises(EdubaoAPIError, match="invalid passport") as ei:
        await client.submit_blocked_account(2, {})
    assert ei.value.status_code == 400 and route.call_count == 1


@respx.mock
async def test_status_false_with_200_is_error():
    respx.post(STEP_URL).respond(200, json={"status": False, "message": "bad lead"})
    client, _ = build(FakeStore())
    with pytest.raises(EdubaoAPIError, match="bad lead"):
        await client.submit_blocked_account(2, {})


@respx.mock
async def test_read_timeout_not_retried():
    route = respx.post(STEP_URL).mock(side_effect=httpx.ReadTimeout("slow"))
    client, _ = build(FakeStore())
    with pytest.raises(EdubaoTransportError):
        await client.submit_blocked_account(1, {})
    assert route.call_count == 1


@respx.mock
async def test_upload_document_multipart():
    route = respx.post(f"{BASE}/api/v1/partners/{PK}/documents-upload").respond(
        json={"doc_id": 4480, "url": "u", "file_name": "f.png", "o_file_name": "Passport.png",
              "mimetype": "image/png", "size": 5, "status": True}
    )
    client, _ = build(FakeStore())
    res = await client.upload_document("passport", 1880, ("Passport.png", b"12345", "image/png"))
    assert res.doc_id == 4480
    req = route.calls[0].request
    assert req.headers["content-type"].startswith("multipart/form-data")
    assert b'name="doc_key"' in req.content and b"12345" in req.content


@respx.mock
async def test_onboarding_chain():
    api = EdubaoAuthAPI(EdubaoHTTP())
    respx.post(f"{BASE}/api/v1/user/signin").respond(
        json={"data": {"access_token": "login", "partner_key": PK, "user_key": PK}, "status": True}
    )
    otp = respx.post(f"{BASE}/api/v1/partners/{PK}/initiate-cred-otp").respond(json={"status": True})
    ver = respx.post(f"{BASE}/api/v1/partners/{PK}/verify-cred-otp").respond(
        json={"user_key": PK, "x_api_key": "pk_x", "oauth_client": {"client_id": "c", "client_secret": "s"}}
    )
    s = await api.sign_in(BASE, "a@b.c", "pw")
    await api.initiate_cred_otp(BASE, s.partner_key, s.access_token)
    creds = await api.verify_cred_otp(BASE, s.partner_key, s.access_token, "123456")
    assert otp.calls[0].request.headers["authorization"] == "Bearer login"
    assert creds.x_api_key == "pk_x" and b"otp=123456" in ver.calls[0].request.content


@respx.mock
async def test_call_recorder_redacts_secrets():
    records = []

    async def rec(r):
        records.append(r)

    respx.post(TOKEN_URL).respond(json={"access_token": "tok2", "expires_in": 7200, "status": True})
    api = EdubaoAuthAPI(EdubaoHTTP(recorder=rec))
    await api.get_access_token(BASE, PK, x_api_key="k", email="a@b.c", password="hunter2",
                               client_id="c", client_secret="s3cret")
    dumped = str(records[0].request_summary) + str(records[0].response_summary)
    assert "hunter2" not in dumped and "s3cret" not in dumped and "tok2" not in dumped


def test_sanitize_nested_and_bytes():
    out = sanitize({"a": [{"password": "x", "ok": 1}], "f": b"abc"})
    assert out == {"a": [{"password": "***", "ok": 1}], "f": "<3 bytes>"}
