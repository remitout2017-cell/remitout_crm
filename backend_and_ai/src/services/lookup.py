from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BlockedAccountLead
from services.leads import LeadNotFound, StepOrderError


async def get_edubao_lead(session: AsyncSession, lead_id: int, *, need_account_id: bool = False) -> BlockedAccountLead:
    """Load a lead that already exists at Edubao (step 1 done)."""
    lead = await session.get(BlockedAccountLead, lead_id)
    if lead is None:
        raise LeadNotFound(f"Lead {lead_id} not found")
    if lead.edubao_lead_id is None:
        raise StepOrderError("Lead has no Edubao id; step 1 has not succeeded")
    if need_account_id and not lead.account_id:
        raise StepOrderError("Lead has no Edubao account_id yet")
    return lead
