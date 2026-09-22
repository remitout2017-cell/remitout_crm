from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.student import Place


class PayerIn(BaseModel):
    id: int | None = None  # our payer id; omit to add a new payer, set to update
    title: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_code: str
    mobile_number: str
    date_of_birth: date
    relationship: str
    nationality: str
    nationality_iso: str
    birth_place: Place
    street_num: str
    additional_address: str = ""
    postal_code: str
    city: str
    state: str
    country: str
    country_iso: str
    transfer_amt: Decimal = Field(gt=0)


class PayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    edubao_payer_id: int | None
    payer_account_id: str | None
    first_name: str
    last_name: str
    email: str
    relationship_to_student: str | None
    transfer_amt: Decimal | None
    created_at: datetime
