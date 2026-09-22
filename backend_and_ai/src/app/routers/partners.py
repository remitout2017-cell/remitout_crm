from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_auth_api, get_cache
from app.schemas.partner import OnboardStart, OnboardVerify, PartnerAccountOut
from core.cache import Cache, keys
from db.models import PartnerAccount
from db.session import get_session
from partners.edubao.onboarding import EdubaoAuthAPI
from services.partner_onboarding import OnboardingService

router = APIRouter(prefix="/partners", tags=["partners"])


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
    acct = await OnboardingService(session, auth_api).verify_otp(account_id, body.otp)
    await session.commit()
    await cache.delete(keys.partner(account_id))
    return acct


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
