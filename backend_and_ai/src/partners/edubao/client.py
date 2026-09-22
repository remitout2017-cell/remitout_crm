from typing import Any

from partners.edubao.auth import TokenManager, TokenStore
from partners.edubao.errors import EdubaoAuthError
from partners.edubao.http import EdubaoHTTP, FileTuple
from partners.edubao.schemas import DocumentUploadResult, LeadStepResult, PayerResult, VerificationResult


class EdubaoPartnerClient:
    """Authenticated Edubao calls (doc sections 4-5) for one partner account.

    Sends x-api-key + Bearer on every call, and retries once with a fresh token on 401.
    """

    def __init__(self, account_id: int, http: EdubaoHTTP, store: TokenStore, tokens: TokenManager):
        self._account_id = account_id
        self._http = http
        self._store = store
        self._tokens = tokens

    async def _call(self, method: str, endpoint: str, **kwargs: Any) -> dict:
        creds = await self._store.load(self._account_id)
        path = f"/api/v1/partners/{creds.partner_key}/{endpoint}"
        token = await self._tokens.get_access_token(self._account_id)
        for attempt in (1, 2):
            headers = {"x-api-key": creds.x_api_key, "Authorization": f"Bearer {token}"}
            try:
                return await self._http.request(
                    method, creds.base_url, path, headers=headers, account_id=self._account_id, **kwargs
                )
            except EdubaoAuthError:
                if attempt == 2:
                    raise
                token = await self._tokens.force_refresh(self._account_id, token)
        raise AssertionError("unreachable")  # pragma: no cover

    async def form_required_data(self) -> dict:
        return (await self._call("GET", "form-required-data")).get("data", {})

    async def submit_blocked_account(self, step: int, payload: dict[str, Any]) -> LeadStepResult:
        """`payload` is sent as-is (JSON), including Edubao's literal keys like `country[iso]`."""
        body = await self._call("POST", "submit-blocked-account", json={"step": step, **payload})
        return LeadStepResult.model_validate(body)

    async def upload_document(self, doc_key: str, lead_id: int, file: FileTuple) -> DocumentUploadResult:
        body = await self._call(
            "POST",
            "documents-upload",
            data={"doc_key": doc_key, "lead_id": str(lead_id)},
            files={"file": file},
        )
        return DocumentUploadResult.model_validate(body)

    async def add_update_payer(self, payload: dict[str, Any]) -> PayerResult:
        body = await self._call("POST", "add-update-payer", json=payload)
        return PayerResult.model_validate(body)

    async def face_verification(
        self, blocked_acc_no: str, doc_type: str, document_id: int, face: FileTuple
    ) -> VerificationResult:
        body = await self._call(
            "POST",
            "face-verification",
            data={"blocked_acc_no": blocked_acc_no, "doc_type": doc_type, "document_id": str(document_id)},
            files={"face": face},
        )
        return VerificationResult.model_validate(body)

    async def document_verification(
        self, blocked_acc_no: str, doc_type: str, document_id: int, document: FileTuple
    ) -> VerificationResult:
        body = await self._call(
            "POST",
            "document-verification",
            data={"blocked_acc_no": blocked_acc_no, "doc_type": doc_type, "document_id": str(document_id)},
            files={"document": document},
        )
        return VerificationResult.model_validate(body)
