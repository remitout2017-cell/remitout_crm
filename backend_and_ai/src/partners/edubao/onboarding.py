from pydantic import ValidationError

from partners.edubao.errors import EdubaoAPIError
from partners.edubao.http import EdubaoHTTP
from partners.edubao.schemas import CredentialsResult, SignInResult, TokenResult

API = "/api/v1"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class EdubaoAuthAPI:
    """The unauthenticated / credential-issuing endpoints (doc section 3)."""

    def __init__(self, http: EdubaoHTTP):
        self._http = http

    async def sign_in(self, base_url: str, email: str, password: str) -> SignInResult:
        body = await self._http.request(
            "POST", base_url, f"{API}/user/signin", data={"email": email, "password": password}
        )
        data = body["data"]
        try:
            return SignInResult.model_validate(data)
        except ValidationError as exc:
            missing = ", ".join(str(e["loc"][0]) for e in exc.errors() if e["type"] == "missing")
            raise EdubaoAPIError(
                f"Login succeeded but Edubao did not return {missing or 'required fields'} for this account "
                f"(user_type={data.get('user_type')!r}, status={data.get('status')!r}, "
                f"user_key={data.get('user_key')!r}, base_url={base_url}). It likely doesn't have Partner API "
                "access enabled on this environment yet — ask Edubao to activate it (or try the other environment).",
                status_code=502,
                body=data,
            ) from exc

    async def initiate_cred_otp(self, base_url: str, partner_key: str, login_token: str) -> None:
        await self._http.request(
            "POST", base_url, f"{API}/partners/{partner_key}/initiate-cred-otp", headers=_bearer(login_token)
        )

    async def verify_cred_otp(
        self, base_url: str, partner_key: str, login_token: str, otp: str
    ) -> CredentialsResult:
        body = await self._http.request(
            "POST",
            base_url,
            f"{API}/partners/{partner_key}/verify-cred-otp",
            headers=_bearer(login_token),
            data={"otp": otp},
        )
        oauth_client = body.pop("oauth_client", None) or {}
        return CredentialsResult.model_validate({**body, **oauth_client})

    async def get_access_token(
        self,
        base_url: str,
        partner_key: str,
        *,
        x_api_key: str,
        email: str,
        password: str,
        client_id: str,
        client_secret: str,
    ) -> TokenResult:
        body = await self._http.request(
            "POST",
            base_url,
            f"{API}/partners/{partner_key}/access-token",
            headers={"x-api-key": x_api_key},
            data={
                "email_id": email,
                "user_password": password,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        return TokenResult.model_validate(body)

    async def refresh_access_token(
        self, base_url: str, partner_key: str, *, x_api_key: str, refresh_token: str
    ) -> TokenResult:
        body = await self._http.request(
            "POST",
            base_url,
            f"{API}/partners/{partner_key}/refresh-access-token",
            headers={"x-api-key": x_api_key},
            data={"refresh_token": refresh_token},
        )
        return TokenResult.model_validate(body)
