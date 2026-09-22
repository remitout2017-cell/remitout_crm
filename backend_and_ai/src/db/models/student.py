from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    geebee_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)

    # identity
    title: Mapped[str | None] = mapped_column(String(10))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str | None] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    diff_maiden_name: Mapped[str | None] = mapped_column(String(100))
    nationality: Mapped[str | None] = mapped_column(String(100))
    nationality_iso: Mapped[str | None] = mapped_column(String(3))
    birth_place: Mapped[dict | None] = mapped_column(JSONB)  # location/city/state/country/iso

    # contact
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone_code: Mapped[str | None] = mapped_column(String(6))
    mobile_no: Mapped[str] = mapped_column(String(20))

    # address
    street_num: Mapped[str | None] = mapped_column(String(255))
    additional_address: Mapped[str | None] = mapped_column(String(255))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    country_iso: Mapped[str | None] = mapped_column(String(3))

    # passport
    passport_num: Mapped[str | None] = mapped_column(String(30))
    passport_issued_date: Mapped[date | None] = mapped_column(Date)
    passport_valid_upto: Mapped[date | None] = mapped_column(Date)
    passport_issue_place: Mapped[dict | None] = mapped_column(JSONB)

    leads: Mapped[list["BlockedAccountLead"]] = relationship(back_populates="student")  # noqa: F821
