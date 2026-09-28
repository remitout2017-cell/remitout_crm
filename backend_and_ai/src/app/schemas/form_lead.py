from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Label for the purpose-specific second document, keyed by the purpose value.
SUPPORTING_DOC_LABELS = {
    "student": "Student University Letter",
    "job_seeker": "Higher Study Certificate",
    "language_learner": "Offer Letter",
    "vocational_training": "Offer Letter",
    "other": "Additional Document",
}

PASSPORT_LABEL = "Student Passport"


class FormLeadDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slot: str
    label: str
    original_file_name: str
    mimetype: str
    size: int
    created_at: datetime


class FormLeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    purpose: str
    email: EmailStr
    phone_number: str
    edubao_account_opened: bool
    created_at: datetime
    documents: list[FormLeadDocumentOut] = []


class FormLeadUpdate(BaseModel):
    edubao_account_opened: bool


class FormLeadPage(BaseModel):
    items: list[FormLeadOut]
    total: int
    page: int
    page_size: int
    pages: int = Field(description="Total number of pages; 0 when there are no results")
