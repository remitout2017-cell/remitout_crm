from collections.abc import Callable

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_cache, get_client_factory
from app.schemas.lead import LeadCreate, LeadOut, LeadUpdate, Step2, Step3, Step4
from core.cache import Cache, keys
from db.session import get_session
from partners.edubao.client import EdubaoPartnerClient
from services.leads import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])


def get_service(
    session: AsyncSession = Depends(get_session),
    client_for: Callable[[int], EdubaoPartnerClient] = Depends(get_client_factory),
) -> LeadService:
    return LeadService(session, client_for)


@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(body: LeadCreate, svc: LeadService = Depends(get_service)):
    """Step 1: create the lead at Edubao using the student's stored contact and address data."""
    lead_id = await svc.create(**body.model_dump())
    await svc.commit()
    return await svc.get(lead_id)


@router.get("", response_model=list[LeadOut])
async def list_leads(
    student_id: int | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 25,
    svc: LeadService = Depends(get_service),
):
    return await svc.list(student_id=student_id, status=status, skip=skip, limit=limit)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: int, svc: LeadService = Depends(get_service), cache: Cache = Depends(get_cache)):
    async def load():
        return LeadOut.model_validate(await svc.get(lead_id)).model_dump(mode="json")

    return await cache.get_or_load(keys.lead(lead_id), load)


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: int, body: LeadUpdate, svc: LeadService = Depends(get_service), cache: Cache = Depends(get_cache)
):
    return await _mutate(lead_id, svc, cache, svc.update(lead_id, app_type=body.app_type, expected_date_arrival=body.expected_date_arrival))


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(lead_id: int, svc: LeadService = Depends(get_service), cache: Cache = Depends(get_cache)):
    try:
        await svc.delete(lead_id)
        await svc.commit()
    finally:
        await cache.delete(keys.lead(lead_id))


async def _mutate(lead_id: int, svc: LeadService, cache: Cache, action, *, touches_student: bool = False):
    """Run a step submission, then invalidate. `finally` matters: a rejected step still commits a
    failed-submission row that shows up in the lead's history."""
    try:
        await action
        await svc.commit()
    finally:
        await cache.delete(keys.lead(lead_id))
    lead = await svc.get(lead_id)
    if touches_student:
        await cache.delete(keys.student(lead.student_id))
    return lead


@router.put("/{lead_id}/steps/2", response_model=LeadOut)
async def step2(
    lead_id: int, body: Step2, svc: LeadService = Depends(get_service), cache: Cache = Depends(get_cache)
):
    return await _mutate(lead_id, svc, cache, svc.submit_step2(lead_id, body), touches_student=True)


@router.put("/{lead_id}/steps/3", response_model=LeadOut)
async def step3(
    lead_id: int, body: Step3, svc: LeadService = Depends(get_service), cache: Cache = Depends(get_cache)
):
    return await _mutate(lead_id, svc, cache, svc.submit_step3(lead_id, body))


@router.put("/{lead_id}/steps/4", response_model=LeadOut)
async def step4(
    lead_id: int, body: Step4, svc: LeadService = Depends(get_service), cache: Cache = Depends(get_cache)
):
    return await _mutate(lead_id, svc, cache, svc.submit_step4(lead_id, body))
