import asyncio
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager, nullcontext
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from partners.edubao.errors import EdubaoAPIError, EdubaoAuthError
from partners.edubao.onboarding import EdubaoAuthAPI

EXPIRY_LEEWAY = timedelta(seconds=60)


@dataclass
class PartnerCredentials:
    """Decrypted view of a partner_accounts row."""

    account_id: int
    base_url: str
    login_email: str
    partner_key: str
    x_api_key: str
    client_id: str
    client_secret: str
    access_token: str | None = None
    refresh_token: str | None = None
    access_token_expires_at: datetime | None = None


class TokenStore(Protocol):
    async def load(self, account_id: int) -> PartnerCredentials: ...

    async def save_tokens(
        self, account_id: int, access_token: str, refresh_token: str | None, expires_at: datetime
    ) -> None: ...


# Returns the partner's Edubao password, or None if we don't hold one.
PasswordProvider = Callable[[PartnerCredentials], Awaitable[str | None]]


def _fresh(creds: PartnerCredentials) -> bool:
    return bool(
        creds.access_token
        and creds.access_token_expires_at
        and creds.access_token_expires_at - EXPIRY_LEEWAY > datetime.now(timezone.utc)
    )


class TokenManager:
    """Hands out a valid OAuth access token per partner account.

    A per-account lock makes concurrent requests share one refresh. Renewal first tries the stored
    refresh token (`refresh-access-token`); if there is none or Edubao rejects it, it falls back to
    re-running `access-token`, which needs the partner's password; without a `password_provider` an
    expired token raises EdubaoAuthError.
    """

    def __init__(
        self,
        store: TokenStore,
        auth_api: EdubaoAuthAPI,
        password_provider: PasswordProvider | None = None,
        lock_factory: Callable[[str], AbstractAsyncContextManager] | None = None,
    ):
        # lock_factory(name) -> async context manager: a cross-process lock so several server
        # instances share one renewal. The per-process asyncio lock below stays as the first gate.
        self._lock_factory = lock_factory
        self._store = store
        self._auth_api = auth_api
        self._password_provider = password_provider
        self._locks: dict[int, asyncio.Lock] = {}

    def _lock(self, account_id: int) -> asyncio.Lock:
        return self._locks.setdefault(account_id, asyncio.Lock())

    async def get_access_token(self, account_id: int) -> str:
        creds = await self._store.load(account_id)
        if _fresh(creds):
            return creds.access_token  # type: ignore[return-value]
        return await self._renew(account_id, stale=creds.access_token)

    async def force_refresh(self, account_id: int, rejected_token: str) -> str:
        """Called after a 401. If another task already renewed, reuse its token."""
        return await self._renew(account_id, stale=rejected_token)

    async def _renew(self, account_id: int, stale: str | None) -> str:
        dist = self._lock_factory(f"token-renew:{account_id}") if self._lock_factory else nullcontext()
        async with self._lock(account_id), dist:
            # Re-read inside the locks: whoever held them before us may have just renewed.
            creds = await self._store.load(account_id)
            if creds.access_token and creds.access_token != stale and _fresh(creds):
                return creds.access_token
            result = None
            if creds.refresh_token:
                try:
                    result = await self._auth_api.refresh_access_token(
                        creds.base_url,
                        creds.partner_key,
                        x_api_key=creds.x_api_key,
                        refresh_token=creds.refresh_token,
                    )
                except (EdubaoAuthError, EdubaoAPIError):
                    result = None  # expired/invalid refresh token: re-authenticate below
            if result is None:
                password = await self._password_provider(creds) if self._password_provider else None
                if not password:
                    raise EdubaoAuthError("Edubao access token expired and no password is available to renew it")
                result = await self._auth_api.get_access_token(
                    creds.base_url,
                    creds.partner_key,
                    x_api_key=creds.x_api_key,
                    email=creds.login_email,
                    password=password,
                    client_id=creds.client_id,
                    client_secret=creds.client_secret,
                )
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=result.expires_in)
            await self._store.save_tokens(account_id, result.access_token, result.refresh_token, expires_at)
            return result.access_token
