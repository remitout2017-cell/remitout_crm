from collections.abc import Callable

from fastapi import APIRouter, Depends

from app.deps import get_cache, get_client_factory
from core.cache import Cache, keys
from core.config import settings
from partners.edubao.client import EdubaoPartnerClient

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/form-data")
async def form_data(
    partner_account_id: int,
    refresh: bool = False,
    cache: Cache = Depends(get_cache),
    client_for: Callable[[int], EdubaoPartnerClient] = Depends(get_client_factory),
):
    """Edubao's form-required-data (app types, titles, document types). Cached; `refresh=true` re-fetches."""
    return await cache.get_or_load(
        keys.form_data(partner_account_id),
        client_for(partner_account_id).form_required_data,
        settings.cache_reference_ttl_seconds,
        refresh=refresh,
    )
