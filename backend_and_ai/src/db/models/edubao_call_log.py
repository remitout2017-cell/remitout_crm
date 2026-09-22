from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class EdubaoCallLog(Base):
    """One row per outbound Edubao request. Payloads must be sanitized (no secrets/files) before insert."""

    __tablename__ = "edubao_call_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_account_id: Mapped[int | None] = mapped_column(ForeignKey("partner_accounts.id", ondelete="SET NULL"), index=True)
    method: Mapped[str] = mapped_column(String(10))
    endpoint: Mapped[str] = mapped_column(String(255))
    status_code: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    request_summary: Mapped[dict | None] = mapped_column(JSONB)
    response_summary: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
