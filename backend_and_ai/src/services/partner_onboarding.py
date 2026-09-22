from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import decrypt, encrypt
from db.models import PartnerAccount
from partners.edubao.errors import EdubaoError
from partners.edubao.onboarding import EdubaoAuthAPI

ENVIRONMENTS = {"staging": lambda: settings.edubao_staging_url, "production": lambda: settings.edubao_production_url}


class OnboardingError(Exception):
    pass


class OnboardingService:
    """Two-phase Edubao onboarding (doc section 3): sign in + send OTP, then verify OTP + fetch tokens.

    The login token lasts 15 minutes, so phase 2 signs in again with the stored password instead of
    persisting it. Callers own the transaction (commit on success).
    """

    def __init__(self, session: AsyncSession, auth_api: EdubaoAuthAPI):
        self._session = session
        self._auth = auth_api

    async def start(self, *, name: str, environment: str, login_email: str, password: str) -> PartnerAccount:
        if environment not in ENVIRONMENTS:
            raise OnboardingError(f"Unknown environment {environment!r}")
        base_url = ENVIRONMENTS[environment]()

        login = await self._auth.sign_in(base_url, login_email, password)

        acct = (
            await self._session.execute(select(PartnerAccount).where(PartnerAccount.partner_key == login.partner_key))
        ).scalar_one_or_none()
        if acct is None:
            acct = PartnerAccount(partner_key=login.partner_key)
            self._session.add(acct)
        acct.name, acct.environment, acct.base_url = name, environment, base_url
        acct.login_email, acct.user_key = login_email, login.user_key
        acct.password_enc = encrypt(password)
        acct.is_active = True
        await self._session.flush()

        await self._auth.initiate_cred_otp(base_url, login.partner_key, login.access_token)
        return acct

    async def verify_otp(self, account_id: int, otp: str) -> PartnerAccount:
        acct = await self._session.get(PartnerAccount, account_id)
        if acct is None or not acct.password_enc or not acct.partner_key:
            raise OnboardingError("Unknown partner account; start onboarding first")
        password = decrypt(acct.password_enc)

        login = await self._auth.sign_in(acct.base_url, acct.login_email, password)  # type: ignore[arg-type]
        creds = await self._auth.verify_cred_otp(acct.base_url, acct.partner_key, login.access_token, otp)
        acct.x_api_key_enc = encrypt(creds.x_api_key)
        acct.client_id = creds.client_id
        acct.client_secret_enc = encrypt(creds.client_secret)

        token = await self._auth.get_access_token(
            acct.base_url,
            acct.partner_key,
            x_api_key=creds.x_api_key,
            email=acct.login_email,
            password=password,  # type: ignore[arg-type]
            client_id=creds.client_id,
            client_secret=creds.client_secret,
        )
        acct.access_token_enc = encrypt(token.access_token)
        acct.refresh_token_enc = encrypt(token.refresh_token)
        acct.access_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token.expires_in)
        await self._session.flush()
        return acct
