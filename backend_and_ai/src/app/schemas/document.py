from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    edubao_doc_id: int | None
    doc_key: str
    original_file_name: str
    mimetype: str
    size: int
    url: str | None
    created_at: datetime


class VerificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    document_id: int | None
    type: str
    result: str | None
    created_at: datetime
