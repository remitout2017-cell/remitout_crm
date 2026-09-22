from collections.abc import Callable
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.schemas.lead import Step2, Step3, Step4
from db.models import BlockedAccountLead, LeadStepSubmission, PartnerAccount, Student
from partners.edubao.client import EdubaoPartnerClient
from partners.edubao.errors import EdubaoAPIError, EdubaoError

STEP1_REQUIRED = [
    "title", "first_name", "last_name", "gender", "street_num", "postal_code", "city", "state",
    "country", "country_iso", "phone_code", "mobile_no", "email",
]


class LeadNotFound(Exception):
    pass


class StepOrderError(Exception):
    pass


class LeadValidationError(Exception):
    pass


def _nested(prefix: str, values: dict[str, Any]) -> dict[str, Any]:
    """Edubao expects literal keys such as `country[iso]` in the JSON body."""
    return {f"{prefix}[{k}]": v for k, v in values.items()}


def _iso(d: date) -> str:
    return d.isoformat()


class LeadService:
    """Drives the 4-step blocked-account submission and keeps local state in sync.

    Local data is only updated after Edubao accepts a step. Every attempt (ok or failed) is
    recorded in lead_step_submissions; failures are committed before the error is re-raised.
    """

    def __init__(self, session: AsyncSession, client_for: Callable[[int], EdubaoPartnerClient]):
        self._s = session
        self._client_for = client_for

    async def commit(self) -> None:
        await self._s.commit()

    # ---- reads -------------------------------------------------------------------------------
    async def get(self, lead_id: int, *, for_update: bool = False) -> BlockedAccountLead:
        q = (
            select(BlockedAccountLead)
            .where(BlockedAccountLead.id == lead_id)
            .options(selectinload(BlockedAccountLead.submissions))
            .execution_options(populate_existing=True)
        )
        if for_update:
            q = q.with_for_update(of=BlockedAccountLead)
        lead = (await self._s.execute(q)).scalar_one_or_none()
        if lead is None:
            raise LeadNotFound(f"Lead {lead_id} not found")
        return lead

    async def list(self, *, student_id: int | None, status: str | None, skip: int, limit: int):
        q = select(BlockedAccountLead).options(selectinload(BlockedAccountLead.submissions))
        if student_id is not None:
            q = q.where(BlockedAccountLead.student_id == student_id)
        if status:
            q = q.where(BlockedAccountLead.status == status)
        q = q.order_by(BlockedAccountLead.id.desc()).offset(skip).limit(min(limit, 100))
        return (await self._s.execute(q)).scalars().all()

    # ---- step 1 ------------------------------------------------------------------------------
    async def create(
        self, *, student_id: int, partner_account_id: int, app_type: int, expected_date_arrival: date
    ) -> int:
        student = await self._s.get(Student, student_id)
        if student is None:
            raise LeadNotFound(f"Student {student_id} not found")
        account = await self._s.get(PartnerAccount, partner_account_id)
        if account is None or not account.is_active or not account.onboarded:
            raise LeadValidationError("Partner account is missing, inactive, or not onboarded")
        missing = [f for f in STEP1_REQUIRED if not getattr(student, f)]
        if missing:
            raise LeadValidationError(f"Student is missing fields required by Edubao: {', '.join(missing)}")

        lead = BlockedAccountLead(
            student_id=student_id, partner_account_id=partner_account_id, status="draft",
            app_type=app_type, expected_date_arrival=expected_date_arrival,
        )
        self._s.add(lead)
        await self._s.flush()

        payload = {
            "app_type": app_type,
            "title": student.title,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "gender": student.gender,
            "street_num": student.street_num,
            "additional_address": student.additional_address or "",
            "postal_code": student.postal_code,
            "city": student.city,
            "state": student.state,
            **_nested("country", {"name": student.country, "iso": student.country_iso}),
            "phone_code": student.phone_code,
            "mobile_no": student.mobile_no,
            "email_id": student.email,
            "expected_date_arrival": _iso(expected_date_arrival),
        }
        result = await self._submit(lead, 1, payload)
        lead.edubao_lead_id = int(result.id)
        lead.account_id = result.account_id
        lead.status = "in_progress"
        return lead.id

    # ---- steps 2-4 ---------------------------------------------------------------------------
    async def submit_step2(self, lead_id: int, data: Step2) -> None:
        lead = await self._begin_step(lead_id, 2)
        student = await self._s.get(Student, lead.student_id)
        payload = {
            "lead_id": lead.edubao_lead_id,
            "diff_maiden_name": data.diff_maiden_name,
            **_nested("nationality", {"name": data.nationality, "iso": data.nationality_iso}),
            "date_of_birth": _iso(data.date_of_birth),
            **_nested("place_country_birth", data.place_of_birth.model_dump()),
            "passport_num": data.passport_num,
            "passport_issued_date": _iso(data.passport_issued_date),
            "passport_valid_upto": _iso(data.passport_valid_upto),
            **_nested("passport_issue_place", data.passport_issue_place.model_dump()),
        }
        await self._submit(lead, 2, payload)
        student.diff_maiden_name = data.diff_maiden_name
        student.nationality, student.nationality_iso = data.nationality, data.nationality_iso
        student.date_of_birth = data.date_of_birth
        student.birth_place = data.place_of_birth.model_dump()
        student.passport_num = data.passport_num
        student.passport_issued_date, student.passport_valid_upto = data.passport_issued_date, data.passport_valid_upto
        student.passport_issue_place = data.passport_issue_place.model_dump()

    async def submit_step3(self, lead_id: int, data: Step3) -> None:
        lead = await self._begin_step(lead_id, 3)
        payload = {
            "lead_id": lead.edubao_lead_id,
            "blocked_acc_amt": str(data.blocked_acc_amt),
            "blocked_acc_duration": str(data.blocked_acc_duration),
            "visa_eligibility_doc_type": data.visa_eligibility_doc_type,
        }
        await self._submit(lead, 3, payload)
        lead.blocked_acc_amt = data.blocked_acc_amt
        lead.blocked_acc_duration = data.blocked_acc_duration
        lead.visa_eligibility_doc_type = data.visa_eligibility_doc_type

    async def submit_step4(self, lead_id: int, data: Step4) -> None:
        lead = await self._begin_step(lead_id, 4)
        if not data.terms_and_conditions:
            raise LeadValidationError("Terms and conditions must be accepted")
        await self._submit(lead, 4, {"lead_id": lead.edubao_lead_id, "terms_and_conditions": True})
        lead.terms_accepted = True
        lead.status = "submitted"

    # ---- internals ---------------------------------------------------------------------------
    async def _begin_step(self, lead_id: int, step: int) -> BlockedAccountLead:
        lead = await self.get(lead_id, for_update=True)  # row lock: no concurrent double-submit
        if step > lead.current_step + 1:
            raise StepOrderError(f"Cannot submit step {step}: lead is at step {lead.current_step}")
        if lead.edubao_lead_id is None:
            raise StepOrderError("Lead has no Edubao id; step 1 has not succeeded")
        if lead.status == "submitted":
            raise StepOrderError("Lead is already submitted")
        return lead

    async def _submit(self, lead: BlockedAccountLead, step: int, payload: dict[str, Any]):
        client = self._client_for(lead.partner_account_id)
        try:
            result = await client.submit_blocked_account(step, payload)
        except EdubaoError as exc:
            self._s.add(
                LeadStepSubmission(
                    lead_id=lead.id, step=step, success=False, request_payload=payload,
                    response_payload={"error": str(exc), "body": exc.body if isinstance(exc, EdubaoAPIError) else None},
                )
            )
            await self._s.commit()  # keep the attempt on record, then surface the error
            raise
        self._s.add(
            LeadStepSubmission(
                lead_id=lead.id, step=step, success=True, request_payload=payload,
                response_payload=result.model_dump(mode="json"),
            )
        )
        lead.current_step = max(lead.current_step, step)
        return result
