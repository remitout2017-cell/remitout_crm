from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.uploads import ValidUpload
from db.models import Document, Verification
from partners.edubao.client import EdubaoPartnerClient
from services.leads import LeadNotFound
from services.lookup import get_edubao_lead


class DocumentService:
    """Synchronous document upload and face/document verification. Callers own the commit."""

    def __init__(self, session: AsyncSession, client_for: Callable[[int], EdubaoPartnerClient]):
        self._s = session
        self._client_for = client_for

    async def commit(self) -> None:
        await self._s.commit()

    async def upload(self, lead_id: int, doc_key: str, file: ValidUpload) -> Document:
        lead = await get_edubao_lead(self._s, lead_id)
        result = await self._client_for(lead.partner_account_id).upload_document(
            doc_key, lead.edubao_lead_id, file.as_tuple()  # type: ignore[arg-type]
        )
        doc = Document(
            lead_id=lead.id, edubao_doc_id=result.doc_id, doc_key=doc_key, file_name=result.file_name,
            original_file_name=file.filename, mimetype=result.mimetype, size=result.size, url=result.url,
        )
        self._s.add(doc)
        await self._s.flush()
        return doc

    async def list(self, lead_id: int) -> list[Document]:
        await get_edubao_lead(self._s, lead_id)
        rows = await self._s.execute(select(Document).where(Document.lead_id == lead_id).order_by(Document.id))
        return list(rows.scalars())

    async def verify(self, lead_id: int, kind: str, document_id: int, doc_type: str | None, file: ValidUpload) -> Verification:
        """kind: 'face' (file is the selfie) or 'document' (file is the document image)."""
        lead = await get_edubao_lead(self._s, lead_id, need_account_id=True)
        doc = await self._s.get(Document, document_id)
        if doc is None or doc.lead_id != lead.id:
            raise LeadNotFound(f"Document {document_id} not found on lead {lead_id}")
        client = self._client_for(lead.partner_account_id)
        call = client.face_verification if kind == "face" else client.document_verification
        result = await call(lead.account_id, doc_type or doc.doc_key, doc.edubao_doc_id, file.as_tuple())  # type: ignore[arg-type]
        ver = Verification(
            lead_id=lead.id, document_id=doc.id, type=kind, result=result.verification_status,
            raw_response=result.model_dump(mode="json"),
        )
        self._s.add(ver)
        await self._s.flush()
        return ver
