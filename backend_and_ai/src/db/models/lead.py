from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin


class BlockedAccountLead(TimestampMixin, Base):
    """One blocked-account application, tracked through Edubao's 4 submission steps."""

    __tablename__ = "blocked_account_leads"
    __table_args__ = (UniqueConstraint("partner_account_id", "edubao_lead_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    partner_account_id: Mapped[int] = mapped_column(ForeignKey("partner_accounts.id"), index=True)

    edubao_lead_id: Mapped[int | None] = mapped_column(Integer)
    account_id: Mapped[str | None] = mapped_column(String(64), unique=True)  # e.g. CX-1880-BA-1235
    current_step: Mapped[int] = mapped_column(SmallInteger, default=0)  # last step accepted by Edubao
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)

    app_type: Mapped[int | None] = mapped_column(Integer)
    expected_date_arrival: Mapped[date | None] = mapped_column(Date)
    blocked_acc_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    blocked_acc_duration: Mapped[int | None] = mapped_column(SmallInteger)  # months
    visa_eligibility_doc_type: Mapped[str | None] = mapped_column(String(20))
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    student: Mapped["Student"] = relationship(back_populates="leads")  # noqa: F821
    submissions: Mapped[list["LeadStepSubmission"]] = relationship(back_populates="lead")
    payers: Mapped[list["Payer"]] = relationship(back_populates="lead")  # noqa: F821
    documents: Mapped[list["Document"]] = relationship(back_populates="lead")  # noqa: F821


class LeadStepSubmission(Base):
    """Audit trail of every step submission attempt, used for retry/resume."""

    __tablename__ = "lead_step_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("blocked_account_leads.id", ondelete="CASCADE"), index=True)
    step: Mapped[int] = mapped_column(SmallInteger)
    success: Mapped[bool] = mapped_column(Boolean)
    request_payload: Mapped[dict] = mapped_column(JSONB)
    response_payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    lead: Mapped[BlockedAccountLead] = relationship(back_populates="submissions")
