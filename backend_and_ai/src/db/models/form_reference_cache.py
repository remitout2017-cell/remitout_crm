from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class FormReferenceCache(Base):
    """Cached response of Edubao's form-required-data (titles, app types, doc types), one per partner."""

    __tablename__ = "form_reference_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_account_id: Mapped[int] = mapped_column(ForeignKey("partner_accounts.id", ondelete="CASCADE"), unique=True)
    data: Mapped[dict] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
