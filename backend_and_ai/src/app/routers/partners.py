from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_auth_api, get_cache, get_client_factory
from app.schemas.partner import OnboardStart, OnboardVerify, PartnerAccountOut
from core.cache import Cache, keys
from db.models import PartnerAccount
from db.session import get_session
from partners.edubao.client import EdubaoPartnerClient
from partners.edubao.errors import EdubaoAPIError
from partners.edubao.onboarding import EdubaoAuthAPI
from services.partner_onboarding import OnboardingService

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get("", response_model=list[PartnerAccountOut])
async def list_partners(session: AsyncSession = Depends(get_session)):
    accounts = (await session.execute(select(PartnerAccount).order_by(PartnerAccount.id.desc()))).scalars().all()
    return accounts


@router.post("/onboard/start", response_model=PartnerAccountOut, status_code=201)
async def start_onboarding(
    body: OnboardStart,
    session: AsyncSession = Depends(get_session),
    auth_api: EdubaoAuthAPI = Depends(get_auth_api),
    cache: Cache = Depends(get_cache),
):
    """Sign in to Edubao and email an OTP to the partner."""
    acct = await OnboardingService(session, auth_api).start(
        name=body.name,
        environment=body.environment,
        login_email=body.login_email,
        password=body.password.get_secret_value(),
    )
    await session.commit()
    await cache.delete(keys.partner(acct.id))
    return acct


@router.post("/onboard/{account_id}/verify-otp", response_model=PartnerAccountOut)
async def verify_otp(
    account_id: int,
    body: OnboardVerify,
    session: AsyncSession = Depends(get_session),
    auth_api: EdubaoAuthAPI = Depends(get_auth_api),
    cache: Cache = Depends(get_cache),
):
    """Exchange the OTP for API credentials and the first access token."""
    try:
        acct = await OnboardingService(session, auth_api).verify_otp(account_id, body.otp)
        await session.commit()
    finally:  # credentials are committed before the token call, so a failure there still changes state
        await cache.delete(keys.partner(account_id))
    return acct


@router.post("/onboard/{account_id}/retry-token", response_model=PartnerAccountOut)
async def retry_token(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    auth_api: EdubaoAuthAPI = Depends(get_auth_api),
    cache: Cache = Depends(get_cache),
):
    """Re-fetch the OAuth token with credentials already issued by OTP verification (no new OTP)."""
    acct = await OnboardingService(session, auth_api).retry_token(account_id)
    await session.commit()
    await cache.delete(keys.partner(account_id))
    return acct


@router.get("/{account_id}/edubao-lead")
async def get_edubao_lead(
    account_id: int,
    lead_id: int | None = None,
    edubao_account_id: str | None = None,
    session: AsyncSession = Depends(get_session),
    client_for: Callable[[int], EdubaoPartnerClient] = Depends(get_client_factory),
):
    """Live lead from Edubao (get-lead) by its `lead_id` or `edubao_account_id` (e.g. CX-01-BA-1235)."""
    if lead_id is None and not edubao_account_id:
        raise HTTPException(422, "Provide lead_id or edubao_account_id")
    if await session.get(PartnerAccount, account_id) is None:
        raise HTTPException(404, "Partner account not found")
    try:
        return await client_for(account_id).get_lead(lead_id=lead_id, account_id=edubao_account_id)
    except EdubaoAPIError as exc:
        # Edubao answers "Lead not found." both for unknown leads and other partners' leads.
        if "not found" in str(exc).lower():
            raise HTTPException(404, "Lead not found") from exc
        raise


@router.get("/{account_id}", response_model=PartnerAccountOut)
async def get_partner(
    account_id: int, session: AsyncSession = Depends(get_session), cache: Cache = Depends(get_cache)
):
    async def load():
        acct = await session.get(PartnerAccount, account_id)
        if acct is None:
            raise HTTPException(404, "Partner account not found")
        return PartnerAccountOut.model_validate(acct).model_dump(mode="json")

    return await cache.get_or_load(keys.partner(account_id), load)
