from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

Mobile = Annotated[str, StringConstraints(pattern=r"^\d{10}$")]  # 10 digits, no country code (that's phone_code)
CountryIso3 = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]  # ISO alpha-3, e.g. IND


class Place(BaseModel):
    location: str
    city: str
    state: str
    country: str
    iso: CountryIso3


class PlaceOut(BaseModel):
    location: str
    city: str
    state: str
    country: str
    iso: str | None = None  # output stays lenient so rows saved before the 3-letter rule still load


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile_no: Mobile
    title: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    phone_code: str | None = None
    street_num: str | None = None
    additional_address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    country_iso: CountryIso3 | None = None


class StudentUpdate(BaseModel):
    """All optional; only provided fields change."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    mobile_no: Mobile | None = None
    title: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    phone_code: str | None = None
    street_num: str | None = None
    additional_address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    country_iso: CountryIso3 | None = None


class StudentOut(StudentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mobile_no: str  # output stays lenient so rows saved before the 10-digit rule still load
    country_iso: str | None = None  # output stays lenient so rows saved before the 3-letter rule still load
    status: str
    diff_maiden_name: str | None = None
    nationality: str | None = None
    nationality_iso: str | None = None
    birth_place: PlaceOut | None = None
    passport_num: str | None = None
    passport_issued_date: date | None = None
    passport_valid_upto: date | None = None
    passport_issue_place: PlaceOut | None = None
    created_at: datetime
