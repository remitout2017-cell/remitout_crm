from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin


class Verification(TimestampMixin, Base):
    __tablename__ = "verifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("blocked_account_leads.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"))
    type: Mapped[str] = mapped_column(String(20))  # face | document
    result: Mapped[str | None] = mapped_column(String(30))  # matched | verified | ...
    raw_response: Mapped[dict | None] = mapped_column(JSONB)
