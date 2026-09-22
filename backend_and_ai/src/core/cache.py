import asyncio
import json
import logging
import random
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from redis.asyncio import Redis, from_url

from core.config import settings

log = logging.getLogger(__name__)

# Delete the lock only if we still own it (it may have expired and been taken by someone else).
_RELEASE = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"


class Cache:
    """Cache-aside on Redis (Upstash). Postgres stays the source of truth.

    Fail-open: if Redis is unset, slow, or down, reads fall through to the DB and writes still
    succeed. A failed *delete* is logged loudly; staleness is then bounded by the TTL.
    Values must be JSON-serialisable (store `model_dump(mode="json")`, not ORM objects).
    """

    def __init__(self, client: Redis | None, prefix: str | None = None, default_ttl: int | None = None):
        self._r = client
        self._prefix = prefix or settings.cache_prefix
        self._ttl = default_ttl or settings.cache_ttl_seconds

    @property
    def enabled(self) -> bool:
        return self._r is not None

    def _k(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    async def get(self, key: str) -> Any | None:
        if not self._r:
            return None
        try:
            raw = await self._r.get(self._k(key))
            return None if raw is None else json.loads(raw)
        except Exception:
            log.warning("cache get failed for %s", key, exc_info=True)
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not self._r:
            return
        ttl = ttl or self._ttl
        ttl += random.randint(0, max(ttl // 10, 1))  # jitter so keys written together don't expire together
        try:
            await self._r.set(self._k(key), json.dumps(value), ex=ttl)  # one command (Upstash bills per command)
        except Exception:
            log.warning("cache set failed for %s", key, exc_info=True)

    async def delete(self, *keys: str) -> None:
        if not self._r or not keys:
            return
        try:
            await self._r.delete(*(self._k(k) for k in keys))
        except Exception:
            log.error("cache delete failed for %s; entries stay stale until TTL", keys, exc_info=True)

    async def get_or_load(
        self, key: str, loader: Callable[[], Awaitable[Any]], ttl: int | None = None, *, refresh: bool = False
    ) -> Any:
        """Hit -> cached value. Miss -> `loader()` (the DB), store the result, return it.
        Loader exceptions (e.g. not found) propagate and nothing is cached."""
        if not refresh:
            cached = await self.get(key)
            if cached is not None:
                return cached
        value = await loader()
        if value is not None:
            await self.set(key, value, ttl)
        return value

    @asynccontextmanager
    async def lock(self, name: str, ttl_ms: int = 60_000, wait_s: float = 30.0) -> AsyncIterator[bool]:
        """Cross-process mutex (SET NX PX + owner-checked release). Yields whether it was acquired.

        Fail-open by design: with Redis unset/down, or after `wait_s`, it yields False and the caller
        proceeds. Callers must therefore re-check state after entering (double-checked locking) and
        treat the lock as an optimisation against duplicate work, not as a safety guarantee.
        `ttl_ms` bounds how long a crashed holder can block others.
        """
        if not self._r:
            yield False
            return
        key, owner = self._k(f"lock:{name}"), uuid.uuid4().hex
        acquired, delay, deadline = False, 0.05, time.monotonic() + wait_s
        while True:
            try:
                acquired = bool(await self._r.set(key, owner, nx=True, px=ttl_ms))
            except Exception:
                log.warning("lock %s: redis unavailable, proceeding without it", name, exc_info=True)
                break
            if acquired or time.monotonic() >= deadline:
                break
            await asyncio.sleep(delay)
            delay = min(delay * 2, 0.5)  # back off: Upstash bills per command
        if not acquired:
            log.warning("lock %s: not acquired, proceeding without it", name)
        try:
            yield acquired
        finally:
            if acquired:
                try:
                    await self._r.eval(_RELEASE, 1, key, owner)
                except Exception:
                    log.warning("lock %s: release failed; it expires after %d ms", name, ttl_ms, exc_info=True)

    async def close(self) -> None:
        if self._r:
            await self._r.aclose()


def make_cache() -> Cache:
    if not settings.redis_url:
        return Cache(None)
    client = from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=2,  # a slow Redis must not stall requests
        socket_connect_timeout=2,
        health_check_interval=30,
    )
    return Cache(client)


class keys:
    student = staticmethod(lambda id_: f"student:{id_}")
    lead = staticmethod(lambda id_: f"lead:{id_}")
    partner = staticmethod(lambda id_: f"partner:{id_}")
    form_data = staticmethod(lambda account_id: f"edubao:form-data:{account_id}")
