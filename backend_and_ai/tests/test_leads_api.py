import os

import httpx
import pytest
from sqlalchemy import text

pytestmark = pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="needs TEST_DATABASE_URL")

BASE = "https://api.edubao.lifeinurl.com"
PK = "p_abc"
SUBMIT = f"{BASE}/api/v1/partners/{PK}/submit-blocked-account"

STUDENT = {
    "first_name": "John", "last_name": "Doe", "email": "john@example.com", "mobile_no": "9090909090",
    "title": "Mr", "gender": "Male", "phone_code": "91", "street_num": "Street 1", "postal_code": "400069",
    "city": "Mumbai", "state": "Maharashtra", "country": "India", "country_iso": "IND",
}
PLACE = {"location": "Zagora, Morocco", "city": "Zagora", "state": "Draa", "country": "Morocco", "iso": "MAR"}
STEP2 = {
    "nationality": "Morocco", "nationality_iso": "MAR", "date_of_birth": "2001-10-20", "place_of_birth": PLACE,
    "passport_num": "DJ5103460", "passport_issued_date": "2020-07-07", "passport_valid_upto": "2029-07-11",
    "passport_issue_place": PLACE,
}
STEP3 = {"blocked_acc_amt": "11904", "blocked_acc_duration": 6, "visa_eligibility_doc_type": "19"}


@pytest.fixture
async def ctx(respx_mock):
    from datetime import datetime, timedelta, timezone

    from app.deps import init_edubao
    from app.main import app
    from core.config import settings
    from core.security import encrypt
    from db.models import PartnerAccount
    from db.session import SessionLocal, engine

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE students, partner_accounts, edubao_call_log RESTART IDENTITY CASCADE"))
    async with SessionLocal() as s, s.begin():
        s.add(PartnerAccount(
            name="p", base_url=BASE, login_email="a@b.co", partner_key=PK, x_api_key_enc=encrypt("k"),
            client_id="c", client_secret_enc=encrypt("s"), access_token_enc=encrypt("tok"),
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))
    settings.admin_api_key = "test-admin"
    init_edubao(app)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://t", headers={"X-Admin-Key": "test-admin"}
    ) as c:
        yield c, respx_mock
    await app.state.edubao_http.aclose()
    await engine.dispose()


def ok(id_=1880):
    return httpx.Response(200, json={"message": "Lead updated successfully", "id": id_, "account_id": "CX-1880-BA-1235", "status": True})


async def new_lead(c, student=STUDENT):
    sid = (await c.post("/students", json=student)).json()["id"]
    return await c.post("/leads", json={"student_id": sid, "partner_account_id": 1, "app_type": 2, "expected_date_arrival": "2025-08-30"})


async def test_full_four_step_flow(ctx):
    c, mock = ctx
    route = mock.post(SUBMIT).mock(return_value=ok())
    r = await new_lead(c)
    assert r.status_code == 201, r.text
    lead = r.json()
    assert lead["edubao_lead_id"] == 1880 and lead["account_id"] == "CX-1880-BA-1235" and lead["current_step"] == 1
    body = route.calls[0].request.content.decode()
    for frag in ('"step":1', '"country[iso]":"IND"', '"email_id":"john@example.com"', '"app_type":2'):
        assert frag in body.replace(" ", "")

    assert (await c.put(f"/leads/{lead['id']}/steps/2", json=STEP2)).json()["current_step"] == 2
    assert 'place_country_birth[city]' in route.calls[1].request.content.decode()
    r = await c.put(f"/leads/{lead['id']}/steps/3", json=STEP3)
    assert r.json()["current_step"] == 3 and r.json()["blocked_acc_duration"] == 6
    r = await c.put(f"/leads/{lead['id']}/steps/4", json={"terms_and_conditions": True})
    assert r.json()["status"] == "submitted" and r.json()["terms_accepted"] is True
    assert sorted(s["step"] for s in r.json()["submissions"]) == [1, 2, 3, 4]

    st = (await c.get(f"/students/{lead['student_id']}")).json()
    assert st["passport_num"] == "DJ5103460" and st["nationality"] == "Morocco"


async def test_cannot_skip_steps_and_no_edubao_call(ctx):
    c, mock = ctx
    route = mock.post(SUBMIT).mock(return_value=ok())
    lead = (await new_lead(c)).json()
    r = await c.put(f"/leads/{lead['id']}/steps/3", json=STEP3)
    assert r.status_code == 409 and route.call_count == 1


async def test_edubao_rejection_is_recorded_and_step_not_advanced(ctx):
    c, mock = ctx
    mock.post(SUBMIT).mock(side_effect=[ok(), httpx.Response(400, json={"message": "invalid passport", "status": False})])
    lead = (await new_lead(c)).json()
    r = await c.put(f"/leads/{lead['id']}/steps/2", json=STEP2)
    assert r.status_code == 400 and "invalid passport" in r.json()["detail"]
    got = (await c.get(f"/leads/{lead['id']}")).json()
    assert got["current_step"] == 1
    assert sorted((s["step"], s["success"]) for s in got["submissions"]) == [(1, True), (2, False)]
    st = (await c.get(f"/students/{lead['student_id']}")).json()
    assert st["passport_num"] is None  # local data untouched on failure


async def test_step1_reports_missing_student_fields(ctx):
    c, mock = ctx
    r = await new_lead(c, {"first_name": "A", "last_name": "B", "email": "a@b.co", "mobile_no": "1"})
    assert r.status_code == 422 and "gender" in r.json()["detail"]


async def test_terms_must_be_true_and_unknown_lead_404(ctx):
    c, mock = ctx
    mock.post(SUBMIT).mock(return_value=ok())
    lead = (await new_lead(c)).json()
    await c.put(f"/leads/{lead['id']}/steps/2", json=STEP2)
    await c.put(f"/leads/{lead['id']}/steps/3", json=STEP3)
    assert (await c.put(f"/leads/{lead['id']}/steps/4", json={"terms_and_conditions": False})).status_code == 422
    assert (await c.get("/leads/999")).status_code == 404
