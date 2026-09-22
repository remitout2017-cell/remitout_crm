from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class Place(BaseModel):
    location: str
    city: str
    state: str
    country: str
    iso: str


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile_no: str
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
    country_iso: str | None = None


class StudentUpdate(BaseModel):
    """All optional; only provided fields change."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    mobile_no: str | None = None
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
    country_iso: str | None = None


class StudentOut(StudentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    nationality: str | None = None
    nationality_iso: str | None = None
    passport_num: str | None = None
    created_at: datetime
