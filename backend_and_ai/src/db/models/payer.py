from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin


class Payer(TimestampMixin, Base):
    __tablename__ = "payers"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("blocked_account_leads.id", ondelete="CASCADE"), index=True)
    edubao_payer_id: Mapped[int | None] = mapped_column(Integer)
    payer_account_id: Mapped[str | None] = mapped_column(String(64))  # e.g. CX-1880-BA-1235p

    title: Mapped[str | None] = mapped_column(String(10))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    phone_code: Mapped[str | None] = mapped_column(String(6))
    mobile_number: Mapped[str] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    relationship_to_student: Mapped[str | None] = mapped_column(String(50))
    nationality: Mapped[str | None] = mapped_column(String(100))
    nationality_iso: Mapped[str | None] = mapped_column(String(3))
    birth_place: Mapped[dict | None] = mapped_column(JSONB)

    street_num: Mapped[str | None] = mapped_column(String(255))
    additional_address: Mapped[str | None] = mapped_column(String(255))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    country_iso: Mapped[str | None] = mapped_column(String(3))

    transfer_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    lead: Mapped["BlockedAccountLead"] = relationship(back_populates="payers")  # noqa: F821
