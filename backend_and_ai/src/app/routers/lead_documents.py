from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_client_factory
from app.schemas.document import DocumentOut, VerificationOut
from app.schemas.payer import PayerIn, PayerOut
from app.uploads import read_upload
from db.session import get_session
from partners.edubao.client import EdubaoPartnerClient
from services.documents import DocumentService
from services.payers import PayerService

router = APIRouter(prefix="/leads/{lead_id}", tags=["lead documents & payers"])

DocKey = Annotated[str, Form(pattern=r"^[a-z0-9_]{1,50}$")]


def doc_service(
    session: AsyncSession = Depends(get_session),
    client_for: Callable[[int], EdubaoPartnerClient] = Depends(get_client_factory),
) -> DocumentService:
    return DocumentService(session, client_for)


def payer_service(
    session: AsyncSession = Depends(get_session),
    client_for: Callable[[int], EdubaoPartnerClient] = Depends(get_client_factory),
) -> PayerService:
    return PayerService(session, client_for)


@router.post("/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    lead_id: int, doc_key: DocKey, file: UploadFile = File(...), svc: DocumentService = Depends(doc_service)
):
    """Upload a PDF/PNG/JPEG (max 2 MB) to Edubao and record its metadata."""
    upload = await read_upload(file)
    doc = await svc.upload(lead_id, doc_key, upload)
    await svc.commit()
    return doc


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(lead_id: int, svc: DocumentService = Depends(doc_service)):
    return await svc.list(lead_id)


@router.post("/verify/face", response_model=VerificationOut, status_code=201)
async def verify_face(
    lead_id: int,
    document_id: Annotated[int, Form()],
    doc_type: Annotated[str | None, Form()] = None,
    file: UploadFile = File(..., description="Selfie to match against the uploaded document"),
    svc: DocumentService = Depends(doc_service),
):
    ver = await svc.verify(lead_id, "face", document_id, doc_type, await read_upload(file))
    await svc.commit()
    return ver


@router.post("/verify/document", response_model=VerificationOut, status_code=201)
async def verify_document(
    lead_id: int,
    document_id: Annotated[int, Form()],
    doc_type: Annotated[str | None, Form()] = None,
    file: UploadFile = File(..., description="The document image to verify"),
    svc: DocumentService = Depends(doc_service),
):
    ver = await svc.verify(lead_id, "document", document_id, doc_type, await read_upload(file))
    await svc.commit()
    return ver


@router.put("/payers", response_model=PayerOut)
async def upsert_payer(lead_id: int, body: PayerIn, svc: PayerService = Depends(payer_service)):
    """Add a payer, or update one when `id` is given."""
    payer = await svc.upsert(lead_id, body)
    await svc.commit()
    return payer


@router.get("/payers", response_model=list[PayerOut])
async def list_payers(lead_id: int, svc: PayerService = Depends(payer_service)):
    return await svc.list(lead_id)
