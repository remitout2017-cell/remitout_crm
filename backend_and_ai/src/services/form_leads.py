from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.schemas.form_lead import PASSPORT_LABEL, SUPPORTING_DOC_LABELS
from app.uploads import ValidUpload
from core.trie import Trie
from db.models import FormLead, FormLeadDocument


class FormLeadService:
    """Public intake-form submissions and the documents attached to them. Callers own the commit."""

    def __init__(self, session: AsyncSession):
        self._s = session

    async def commit(self) -> None:
        await self._s.commit()

    async def create(
        self, full_name: str, purpose: str, email: str, phone_number: str, passport: ValidUpload, supporting: ValidUpload
    ) -> FormLead:
        lead = FormLead(full_name=full_name, purpose=purpose, email=email, phone_number=phone_number)
        lead.documents = [
            FormLeadDocument(
                slot="passport", label=PASSPORT_LABEL, original_file_name=passport.filename,
                mimetype=passport.mimetype, size=passport.size, content=passport.content,
            ),
            FormLeadDocument(
                slot="supporting", label=SUPPORTING_DOC_LABELS[purpose], original_file_name=supporting.filename,
                mimetype=supporting.mimetype, size=supporting.size, content=supporting.content,
            ),
        ]
        self._s.add(lead)
        await self._s.flush()
        return lead

    async def search(self, query: str | None, page: int, page_size: int) -> tuple[list[FormLead], int]:
        """Page through form leads, optionally narrowed by a name/phone/email prefix via a Trie lookup."""
        if query and query.strip():
            ids = await self._matching_ids(query.strip().lower())
            total = len(ids)
            if not total:
                return [], 0
            page_ids = ids[(page - 1) * page_size: page * page_size]
            if not page_ids:
                return [], total
            rows = await self._s.execute(
                select(FormLead).options(selectinload(FormLead.documents)).where(FormLead.id.in_(page_ids))
            )
            by_id = {lead.id: lead for lead in rows.scalars()}
            return [by_id[i] for i in page_ids if i in by_id], total

        total = await self._s.scalar(select(func.count()).select_from(FormLead)) or 0
        rows = await self._s.execute(
            select(FormLead).options(selectinload(FormLead.documents)).order_by(FormLead.id.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        return list(rows.scalars()), total

    async def _matching_ids(self, query: str) -> list[int]:
        """Builds a Trie over every lead's name tokens, phone number and email, then returns a prefix match."""
        trie = Trie()
        rows = await self._s.execute(select(FormLead.id, FormLead.full_name, FormLead.phone_number, FormLead.email))
        for id_, name, phone, email in rows.all():
            for token in name.lower().split():
                trie.insert(token, id_)
            trie.insert(phone.lower(), id_)
            trie.insert(email.lower(), id_)
        matched = trie.search_prefix(query)
        return sorted(matched, reverse=True)  # newest-first, matching the default (no-search) ordering

    async def update_status(self, form_lead_id: int, edubao_account_opened: bool) -> FormLead | None:
        lead = await self._s.get(FormLead, form_lead_id, options=[selectinload(FormLead.documents)])
        if lead is None:
            return None
        lead.edubao_account_opened = edubao_account_opened
        await self._s.flush()
        return lead

    async def delete(self, form_lead_id: int) -> bool:
        lead = await self._s.get(FormLead, form_lead_id)
        if lead is None:
            return False
        await self._s.delete(lead)
        await self._s.flush()
        return True

    async def get_document(self, form_lead_id: int, document_id: int) -> FormLeadDocument | None:
        doc = await self._s.get(FormLeadDocument, document_id)
        if doc is None or doc.form_lead_id != form_lead_id:
            return None
        return doc
