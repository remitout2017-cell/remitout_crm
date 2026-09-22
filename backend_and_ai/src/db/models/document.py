from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin


class Document(TimestampMixin, Base):
    """A file uploaded to Edubao. We keep metadata + Edubao's URL, not the bytes."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("blocked_account_leads.id", ondelete="CASCADE"), index=True)
    edubao_doc_id: Mapped[int | None] = mapped_column(Integer)
    doc_key: Mapped[str] = mapped_column(String(50))  # e.g. "passport"
    file_name: Mapped[str] = mapped_column(String(255))
    original_file_name: Mapped[str] = mapped_column(String(255))
    mimetype: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(BigInteger)
    url: Mapped[str | None] = mapped_column(Text)

    lead: Mapped["BlockedAccountLead"] = relationship(back_populates="documents")  # noqa: F821
