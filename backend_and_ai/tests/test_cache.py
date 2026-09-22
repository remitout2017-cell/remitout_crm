import fakeredis
import pytest

from core.cache import Cache


@pytest.fixture
def redis():
    return fakeredis.FakeAsyncRedis(decode_responses=True)


async def test_miss_loads_then_hit_skips_loader(redis):
    cache, calls = Cache(redis, prefix="t"), []

    async def loader():
        calls.append(1)
        return {"a": 1}

    assert await cache.get_or_load("k", loader) == {"a": 1}
    assert await cache.get_or_load("k", loader) == {"a": 1}
    assert len(calls) == 1
    assert await redis.get("t:k") is not None


async def test_ttl_is_set_with_jitter_bounds(redis):
    cache = Cache(redis, prefix="t", default_ttl=100)
    await cache.set("k", 1)
    assert 100 <= await redis.ttl("t:k") <= 110


async def test_delete_forces_reload(redis):
    cache, n = Cache(redis, prefix="t"), {"v": 0}

    async def loader():
        n["v"] += 1
        return n["v"]

    assert await cache.get_or_load("k", loader) == 1
    await cache.delete("k")
    assert await cache.get_or_load("k", loader) == 2


async def test_loader_error_not_cached(redis):
    cache = Cache(redis, prefix="t")

    async def boom():
        raise LookupError("nope")

    with pytest.raises(LookupError):
        await cache.get_or_load("k", boom)
    assert await redis.exists("t:k") == 0


async def test_refresh_bypasses_cache(redis):
    cache = Cache(redis, prefix="t")
    await cache.set("k", "old")

    async def loader():
        return "new"

    assert await cache.get_or_load("k", loader, refresh=True) == "new"
    assert await cache.get("k") == "new"


async def test_disabled_cache_always_hits_loader():
    cache = Cache(None)
    assert not cache.enabled

    async def loader():
        return 7

    assert await cache.get_or_load("k", loader) == 7
    await cache.delete("k")  # no-op, no error


class BrokenRedis:
    async def get(self, *a, **k):
        raise ConnectionError("down")

    set = delete = get


async def test_redis_down_fails_open_to_loader():
    cache = Cache(BrokenRedis())  # type: ignore[arg-type]

    async def loader():
        return {"from": "db"}

    assert await cache.get_or_load("k", loader) == {"from": "db"}
    await cache.delete("k")  # logged, not raised
