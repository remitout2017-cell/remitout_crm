from pydantic import BaseModel, ConfigDict


class _Lenient(BaseModel):
    """Edubao's payloads aren't fully documented; keep unknown fields instead of failing."""

    model_config = ConfigDict(extra="allow")


class SignInResult(_Lenient):
    access_token: str
    partner_key: str
    user_key: str | None = None
    partner_id: int | None = None
    expires_in: str | int | None = None


class CredentialsResult(_Lenient):
    user_key: str | None = None
    x_api_key: str
    client_id: str
    client_secret: str


class TokenResult(_Lenient):
    access_token: str
    refresh_token: str | None = None
    expires_in: int = 7200


class LeadStepResult(_Lenient):
    id: int | str
    account_id: str | None = None
    message: str | None = None


class DocumentUploadResult(_Lenient):
    doc_id: int
    url: str | None = None
    file_name: str
    o_file_name: str
    mimetype: str
    size: int


class PayerResult(_Lenient):
    payer_id: int
    account_id: str | None = None
    message: str | None = None


class VerificationResult(_Lenient):
    verification_status: str
