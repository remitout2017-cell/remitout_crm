import asyncio

import fakeredis
import httpx
import pytest
import respx

from core.cache import Cache
from partners.edubao.auth import TokenManager
from partners.edubao.client import EdubaoPartnerClient
from partners.edubao.http import EdubaoHTTP
from partners.edubao.onboarding import EdubaoAuthAPI
from test_edubao import BASE, PK, STEP_URL, TOKEN_URL, FakeStore, pw


@pytest.fixture
def server():
    return fakeredis.FakeServer()


def cache_on(server) -> Cache:
    return Cache(fakeredis.FakeAsyncRedis(server=server, decode_responses=True), prefix="t")


def instance(store, cache):
    """One 'server process': its own HTTP client + TokenManager (own asyncio locks), shared store."""
    http = EdubaoHTTP()
    lf = (lambda name: cache.lock(name)) if cache else None
    tokens = TokenManager(store, EdubaoAuthAPI(http), pw, lock_factory=lf)
    return EdubaoPartnerClient(1, http, store, tokens)


async def slow_token(request):
    await asyncio.sleep(0.2)  # renewal in flight long enough for the other instance to start its own
    return httpx.Response(200, json={"access_token": "tok2", "expires_in": 7200, "status": True})


@respx.mock
async def test_control_without_shared_lock_two_instances_both_renew():
    store = FakeStore(expires_in=-5)
    tok = respx.post(TOKEN_URL).mock(side_effect=slow_token)
    respx.post(STEP_URL).respond(json={"id": 1, "status": True})
    a, b = instance(store, None), instance(store, None)
    await asyncio.gather(a.submit_blocked_account(1, {}), b.submit_blocked_account(1, {}))
    assert tok.call_count == 2  # the problem being fixed


@respx.mock
async def test_shared_lock_makes_instances_share_one_renewal(server):
    store = FakeStore(expires_in=-5)
    tok = respx.post(TOKEN_URL).mock(side_effect=slow_token)
    respx.post(STEP_URL).respond(json={"id": 1, "status": True})
    a, b = instance(store, cache_on(server)), instance(store, cache_on(server))
    await asyncio.gather(*(c.submit_blocked_account(1, {}) for c in (a, b, a, b)))
    assert tok.call_count == 1 and store.saves == 1


async def test_lock_is_mutually_exclusive(server):
    c1, c2, order = cache_on(server), cache_on(server), []

    async def worker(cache, tag):
        async with cache.lock("x") as got:
            assert got
            order.append(f"{tag}-in")
            await asyncio.sleep(0.15)
            order.append(f"{tag}-out")

    await asyncio.gather(worker(c1, "a"), worker(c2, "b"))
    first, second = order[0][0], order[2][0]
    assert first != second and order == [f"{first}-in", f"{first}-out", f"{second}-in", f"{second}-out"]


async def test_release_only_deletes_own_lock(server):
    c = cache_on(server)
    r = c._r
    async with c.lock("x", ttl_ms=50) as got:
        assert got
        await asyncio.sleep(0.1)  # our lock expires...
        await r.set("t:lock:x", "someone-else")  # ...and another owner takes it
    assert await r.get("t:lock:x") == "someone-else"  # our release must not remove it


async def test_crashed_holder_lock_expires(server):
    c = cache_on(server)
    await c._r.set("t:lock:x", "dead-process", px=100)
    async with c.lock("x", wait_s=2) as got:
        assert got  # acquired once the dead holder's TTL passed


async def test_wait_timeout_proceeds_without_lock(server):
    c = cache_on(server)
    await c._r.set("t:lock:x", "other")
    async with c.lock("x", wait_s=0.2) as got:
        assert got is False


async def test_lock_fails_open_when_redis_down_or_disabled():
    class Broken:
        async def set(self, *a, **k):
            raise ConnectionError("down")

    async with Cache(Broken()).lock("x") as got:  # type: ignore[arg-type]
        assert got is False
    async with Cache(None).lock("x") as got:
        assert got is False


async def test_lock_released_after_exception(server):
    c = cache_on(server)
    with pytest.raises(RuntimeError):
        async with c.lock("x"):
            raise RuntimeError("boom")
    assert await c._r.exists("t:lock:x") == 0
