from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.payer import PayerIn
from db.models import Payer
from partners.edubao.client import EdubaoPartnerClient
from services.leads import LeadNotFound
from services.lookup import get_edubao_lead


class PayerService:
    def __init__(self, session: AsyncSession, client_for: Callable[[int], EdubaoPartnerClient]):
        self._s = session
        self._client_for = client_for

    async def commit(self) -> None:
        await self._s.commit()

    async def list(self, lead_id: int) -> list[Payer]:
        await get_edubao_lead(self._s, lead_id)
        rows = await self._s.execute(select(Payer).where(Payer.lead_id == lead_id).order_by(Payer.id))
        return list(rows.scalars())

    async def upsert(self, lead_id: int, data: PayerIn) -> Payer:
        lead = await get_edubao_lead(self._s, lead_id)
        payer = None
        if data.id is not None:
            payer = await self._s.get(Payer, data.id)
            if payer is None or payer.lead_id != lead.id:
                raise LeadNotFound(f"Payer {data.id} not found on lead {lead_id}")

        bp = data.birth_place
        payload = {
            "title": data.title,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "email_id": data.email,
            "mobile_number": data.mobile_number,
            "phone_code": data.phone_code,
            "date_of_birth": data.date_of_birth.isoformat(),
            "street_num": data.street_num,
            "additional_address": data.additional_address,
            "relationship": data.relationship,
            "city": data.city,
            "state": data.state,
            "country": data.country,
            "country_iso": data.country_iso,
            "nationality": data.nationality,
            "nationality_iso": data.nationality_iso,
            "birth_place[description]": bp.location,
            "birth_place[location]": bp.location,
            "birth_place[city]": bp.city,
            "birth_place[state]": bp.state,
            "birth_place[country]": bp.country,
            "birth_place[iso]": bp.iso,
            "lead_id": lead.edubao_lead_id,
            "transfer_amt": str(data.transfer_amt),
            "postal_code": data.postal_code,
            "payer_id": payer.edubao_payer_id if payer else None,
        }
        result = await self._client_for(lead.partner_account_id).add_update_payer(payload)

        if payer is None:
            payer = Payer(lead_id=lead.id)
            self._s.add(payer)
        payer.edubao_payer_id = result.payer_id
        payer.payer_account_id = result.account_id
        payer.title, payer.first_name, payer.last_name = data.title, data.first_name, data.last_name
        payer.email, payer.phone_code, payer.mobile_number = data.email, data.phone_code, data.mobile_number
        payer.date_of_birth, payer.relationship_to_student = data.date_of_birth, data.relationship
        payer.nationality, payer.nationality_iso = data.nationality, data.nationality_iso
        payer.birth_place = bp.model_dump()
        payer.street_num, payer.additional_address, payer.postal_code = data.street_num, data.additional_address, data.postal_code
        payer.city, payer.state, payer.country, payer.country_iso = data.city, data.state, data.country, data.country_iso
        payer.transfer_amt = data.transfer_amt
        await self._s.flush()
        return payer
