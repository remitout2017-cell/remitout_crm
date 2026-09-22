import os

import fakeredis
import httpx
import pytest
from sqlalchemy import text

from core.cache import Cache, keys
from test_leads_api import PK, BASE, PLACE, STEP2, SUBMIT, ctx, new_lead, ok  # noqa: F401  (ctx is a fixture)

pytestmark = pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="needs TEST_DATABASE_URL")


@pytest.fixture
async def cached(ctx):
    from app.main import app

    c, mock = ctx
    redis = fakeredis.FakeAsyncRedis(decode_responses=True)
    app.state.cache = Cache(redis, prefix="t")
    yield c, mock, redis
    await redis.aclose()


async def db(sql, **params):
    from db.session import engine

    async with engine.begin() as conn:
        await conn.execute(text(sql), params)


async def test_student_miss_fills_cache_and_hit_skips_db(cached):
    c, mock, redis = cached
    sid = (await c.post("/students", json={"first_name": "A", "last_name": "B", "email": "a@b.co", "mobile_no": "1"})).json()["id"]
    assert await redis.exists(f"t:{keys.student(sid)}") == 0
    assert (await c.get(f"/students/{sid}")).json()["first_name"] == "A"  # miss -> DB -> cache
    assert await redis.exists(f"t:{keys.student(sid)}") == 1
    await db("UPDATE students SET first_name='Sneaky' WHERE id=:i", i=sid)  # bypass the API
    assert (await c.get(f"/students/{sid}")).json()["first_name"] == "A"  # served from cache
    assert 300 <= await redis.ttl(f"t:{keys.student(sid)}") <= 330


async def test_student_patch_invalidates_then_next_read_refills(cached):
    c, mock, redis = cached
    sid = (await c.post("/students", json={"first_name": "A", "last_name": "B", "email": "a@b.co", "mobile_no": "1"})).json()["id"]
    await c.get(f"/students/{sid}")
    r = await c.patch(f"/students/{sid}", json={"first_name": "Z"})
    assert r.json()["first_name"] == "Z" and await redis.exists(f"t:{keys.student(sid)}") == 0
    assert (await c.get(f"/students/{sid}")).json()["first_name"] == "Z"
    assert await redis.exists(f"t:{keys.student(sid)}") == 1


async def test_404_is_not_cached(cached):
    c, mock, redis = cached
    assert (await c.get("/students/999")).status_code == 404
    assert await redis.keys("*") == []


async def test_lead_cache_invalidated_by_steps_including_failures(cached):
    c, mock, redis = cached
    mock.post(SUBMIT).mock(side_effect=[ok(), httpx.Response(400, json={"message": "bad", "status": False}), ok()])
    lead = (await new_lead(c)).json()
    lk, sk = f"t:{keys.lead(lead['id'])}", f"t:{keys.student(lead['student_id'])}"

    await c.get(f"/leads/{lead['id']}")
    await c.get(f"/students/{lead['student_id']}")
    assert await redis.exists(lk) == 1 and await redis.exists(sk) == 1

    assert (await c.put(f"/leads/{lead['id']}/steps/2", json=STEP2)).status_code == 400
    assert await redis.exists(lk) == 0  # failed attempt adds a submission row -> must invalidate
    assert await redis.exists(sk) == 1  # student untouched by a failed step
    assert len((await c.get(f"/leads/{lead['id']}")).json()["submissions"]) == 2

    assert (await c.put(f"/leads/{lead['id']}/steps/2", json=STEP2)).status_code == 200
    assert await redis.exists(lk) == 0 and await redis.exists(sk) == 0  # success changes the student too
    assert (await c.get(f"/students/{lead['student_id']}")).json()["passport_num"] == "DJ5103460"
    assert (await c.get(f"/leads/{lead['id']}")).json()["current_step"] == 2


async def test_partner_status_invalidated_on_onboarding_and_token_refresh(cached):
    from datetime import datetime, timedelta, timezone

    from app.main import app

    c, mock, redis = cached
    r1 = await c.get("/partners/1")
    assert r1.status_code == 200 and await redis.exists(f"t:{keys.partner(1)}") == 1
    await app.state.edubao_store.save_tokens(1, "new", None, datetime.now(timezone.utc) + timedelta(hours=2))
    assert await redis.exists(f"t:{keys.partner(1)}") == 0
    assert (await c.get("/partners/1")).json()["access_token_expires_at"] != r1.json()["access_token_expires_at"]


async def test_form_data_cached_and_refresh_param(cached):
    c, mock, redis = cached
    route = mock.get(f"{BASE}/api/v1/partners/{PK}/form-required-data").mock(
        side_effect=[httpx.Response(200, json={"status": True, "data": {"v": 1}}), httpx.Response(200, json={"status": True, "data": {"v": 2}})]
    )
    assert (await c.get("/reference/form-data", params={"partner_account_id": 1})).json() == {"v": 1}
    assert (await c.get("/reference/form-data", params={"partner_account_id": 1})).json() == {"v": 1}
    assert route.call_count == 1
    assert (await c.get("/reference/form-data", params={"partner_account_id": 1, "refresh": True})).json() == {"v": 2}
    assert 3600 <= await redis.ttl(f"t:{keys.form_data(1)}") <= 3960
