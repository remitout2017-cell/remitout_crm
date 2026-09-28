from sqlalchemy import BigInteger, Boolean, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

PURPOSES = ("student", "job_seeker", "language_learner", "vocational_training", "other")


class FormLead(TimestampMixin, Base):
    """A prospective student's self-submitted intake form (public 'Upload Document' page)."""

    __tablename__ = "form_leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200))
    purpose: Mapped[str] = mapped_column(String(30), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone_number: Mapped[str] = mapped_column(String(30), index=True)
    # Whether the Edubao (partner) account has been opened for this lead — admin marks it done manually.
    edubao_account_opened: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    documents: Mapped[list["FormLeadDocument"]] = relationship(
        back_populates="form_lead", cascade="all, delete-orphan", order_by="FormLeadDocument.id"
    )


class FormLeadDocument(TimestampMixin, Base):
    """One uploaded file for a form lead. Bytes live in Postgres — this app keeps no local disk/S3 storage."""

    __tablename__ = "form_lead_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    form_lead_id: Mapped[int] = mapped_column(ForeignKey("form_leads.id", ondelete="CASCADE"), index=True)
    slot: Mapped[str] = mapped_column(String(20))  # "passport" | "supporting"
    label: Mapped[str] = mapped_column(String(100))
    original_file_name: Mapped[str] = mapped_column(String(255))
    mimetype: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(BigInteger)
    content: Mapped[bytes] = mapped_column(LargeBinary)

    form_lead: Mapped["FormLead"] = relationship(back_populates="documents")
