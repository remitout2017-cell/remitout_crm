import math
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin
from app.schemas.form_lead import FormLeadOut, FormLeadPage, FormLeadUpdate
from app.uploads import read_upload
from db.models.form_lead import PURPOSES
from db.session import get_session
from services.form_leads import FormLeadService

# Public intake form (no admin key) + an admin-only listing/download of what students submitted.
router = APIRouter(prefix="/form-leads", tags=["form leads"])

Purpose = Annotated[str, Form(pattern=r"^(" + "|".join(PURPOSES) + r")$")]


def form_lead_service(session: AsyncSession = Depends(get_session)) -> FormLeadService:
    return FormLeadService(session)


@router.post("", response_model=FormLeadOut, status_code=201)
async def submit_form_lead(
    full_name: Annotated[str, Form(min_length=1, max_length=200)],
    purpose: Purpose,
    email: Annotated[str, Form()],
    phone_number: Annotated[str, Form(pattern=r"^\d{10}$")],
    passport_file: UploadFile = File(..., description="Student Passport"),
    supporting_file: UploadFile = File(..., description="Purpose-specific supporting document"),
    svc: FormLeadService = Depends(form_lead_service),
):
    """Public: a prospective student submits their details and two documents (PDF/PNG/JPEG, max 2 MB each)."""
    passport = await read_upload(passport_file)
    supporting = await read_upload(supporting_file)
    lead = await svc.create(full_name, purpose, email, phone_number, passport, supporting)
    await svc.commit()
    return lead


@router.get("", response_model=FormLeadPage, dependencies=[Depends(require_admin)])
async def list_form_leads(
    search: str | None = Query(None, description="Prefix match against name, phone number or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100, description="Sized to fit one screen of cards on the frontend"),
    svc: FormLeadService = Depends(form_lead_service),
):
    items, total = await svc.search(search, page, page_size)
    pages = math.ceil(total / page_size) if total else 0
    return FormLeadPage(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.patch("/{form_lead_id}", response_model=FormLeadOut, dependencies=[Depends(require_admin)])
async def update_form_lead(form_lead_id: int, body: FormLeadUpdate, svc: FormLeadService = Depends(form_lead_service)):
    """Currently just the Edubao-account-opened toggle, so the admin can mark that step done."""
    lead = await svc.update_status(form_lead_id, body.edubao_account_opened)
    if lead is None:
        raise HTTPException(404, "Form lead not found")
    await svc.commit()
    return lead


@router.delete("/{form_lead_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_form_lead(form_lead_id: int, svc: FormLeadService = Depends(form_lead_service)):
    deleted = await svc.delete(form_lead_id)
    if not deleted:
        raise HTTPException(404, "Form lead not found")
    await svc.commit()


@router.get("/{form_lead_id}/documents/{document_id}/file", dependencies=[Depends(require_admin)])
async def download_form_lead_document(form_lead_id: int, document_id: int, svc: FormLeadService = Depends(form_lead_service)):
    doc = await svc.get_document(form_lead_id, document_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    return Response(
        content=doc.content, media_type=doc.mimetype,
        headers={"Content-Disposition": f'inline; filename="{doc.original_file_name}"'},
    )
