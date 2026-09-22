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
        return SignInResult.model_validate(body["data"])

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
