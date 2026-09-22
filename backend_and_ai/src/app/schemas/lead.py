from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.student import Place


class LeadCreate(BaseModel):
    """Step 1: student's contact/address data is read from the student record."""

    student_id: int
    partner_account_id: int
    app_type: int  # from Edubao's form-required-data
    expected_date_arrival: date


class Step2(BaseModel):
    diff_maiden_name: str = ""
    nationality: str
    nationality_iso: str
    date_of_birth: date
    place_of_birth: Place
    passport_num: str
    passport_issued_date: date
    passport_valid_upto: date
    passport_issue_place: Place


class Step3(BaseModel):
    blocked_acc_amt: Decimal = Field(gt=0)
    blocked_acc_duration: int = Field(gt=0)  # months
    visa_eligibility_doc_type: str  # from form-required-data


class Step4(BaseModel):
    terms_and_conditions: bool


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step: int
    success: bool
    response_payload: dict | None
    created_at: datetime


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    partner_account_id: int
    edubao_lead_id: int | None
    account_id: str | None
    current_step: int
    status: str
    app_type: int | None
    expected_date_arrival: date | None
    blocked_acc_amt: Decimal | None
    blocked_acc_duration: int | None
    visa_eligibility_doc_type: str | None
    terms_accepted: bool
    created_at: datetime
    submissions: list[SubmissionOut] = []
