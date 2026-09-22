from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, SecretStr


class OnboardStart(BaseModel):
    name: str
    environment: Literal["staging", "production"] = "staging"
    login_email: EmailStr
    password: SecretStr  # stored encrypted; never returned


class OnboardVerify(BaseModel):
    otp: str


class PartnerAccountOut(BaseModel):
    """Deliberately excludes every secret column."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    environment: str
    login_email: str
    partner_key: str | None
    is_active: bool
    access_token_expires_at: datetime | None
    onboarded: bool
