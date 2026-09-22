from collections.abc import Awaitable, Callable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.security import decrypt, encrypt
from db.models import EdubaoCallLog, PartnerAccount
from partners.edubao.auth import PartnerCredentials
from partners.edubao.errors import EdubaoError
from partners.edubao.recording import CallRecord


class DbTokenStore:
    """TokenStore backed by partner_accounts. Uses its own short transactions so tokens are
    committed even if the calling request later rolls back."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        on_change: Callable[[int], Awaitable[None]] | None = None,
    ):
        self._sf = session_factory
        self._on_change = on_change  # e.g. drop cached partner status when tokens rotate

    async def load(self, account_id: int) -> PartnerCredentials:
        async with self._sf() as session:
            acct = await session.get(PartnerAccount, account_id)
        if acct is None or not acct.is_active:
            raise EdubaoError(f"Partner account {account_id} not found or inactive")
        if not (acct.partner_key and acct.x_api_key_enc and acct.client_id and acct.client_secret_enc):
            raise EdubaoError(f"Partner account {account_id} has not completed onboarding")
        return PartnerCredentials(
            account_id=acct.id,
            base_url=acct.base_url,
            login_email=acct.login_email,
            partner_key=acct.partner_key,
            x_api_key=decrypt(acct.x_api_key_enc),  # type: ignore[arg-type]
            client_id=acct.client_id,
            client_secret=decrypt(acct.client_secret_enc),  # type: ignore[arg-type]
            access_token=decrypt(acct.access_token_enc),
            refresh_token=decrypt(acct.refresh_token_enc),
            access_token_expires_at=acct.access_token_expires_at,
        )

    async def save_tokens(
        self, account_id: int, access_token: str, refresh_token: str | None, expires_at: datetime
    ) -> None:
        async with self._sf() as session, session.begin():
            acct = await session.get(PartnerAccount, account_id)
            acct.access_token_enc = encrypt(access_token)
            acct.refresh_token_enc = encrypt(refresh_token)
            acct.access_token_expires_at = expires_at
        if self._on_change:
            await self._on_change(account_id)


def db_call_recorder(session_factory: async_sessionmaker[AsyncSession]):
    async def record(rec: CallRecord) -> None:
        async with session_factory() as session, session.begin():
            session.add(
                EdubaoCallLog(
                    partner_account_id=rec.account_id,
                    method=rec.method,
                    endpoint=rec.endpoint,
                    status_code=rec.status_code,
                    latency_ms=rec.latency_ms,
                    request_summary=rec.request_summary,
                    response_summary=rec.response_summary if isinstance(rec.response_summary, dict) else None,
                    error=rec.error,
                )
            )

    return record


def db_password_provider(session_factory: async_sessionmaker[AsyncSession]):
    """PasswordProvider for TokenManager: the partner's stored (encrypted) Edubao password."""

    async def provide(creds: PartnerCredentials) -> str | None:
        async with session_factory() as session:
            acct = await session.get(PartnerAccount, creds.account_id)
        return decrypt(acct.password_enc) if acct else None

    return provide
