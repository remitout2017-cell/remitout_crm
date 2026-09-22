import time
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from partners.edubao.errors import EdubaoAPIError, EdubaoAuthError, EdubaoError, EdubaoTransportError
from partners.edubao.recording import CallRecord, CallRecorder, sanitize

# (filename, bytes, content_type); bytes only, so the body can be re-sent on retry.
FileTuple = tuple[str, bytes, str]


class EdubaoHTTP:
    """Thin httpx wrapper: retries, error mapping, call recording. Knows nothing about auth."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        recorder: CallRecorder | None = None,
        max_attempts: int = 3,
    ):
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
        self._recorder = recorder
        self._max_attempts = max_attempts

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        base_url: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: dict | None = None,
        files: dict[str, FileTuple] | None = None,
        account_id: int | None = None,
    ) -> dict:
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=0.5, max=4),
            retry=retry_if_exception(lambda e: isinstance(e, EdubaoError) and e.retryable),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                return await self._once(method, base_url, path, headers, json, data, files, account_id)
        raise AssertionError("unreachable")  # pragma: no cover

    async def _once(self, method, base_url, path, headers, json, data, files, account_id) -> dict:
        started = time.monotonic()
        status: int | None = None
        body: Any = None
        error: str | None = None
        try:
            try:
                resp = await self._client.request(
                    method, base_url.rstrip("/") + path, headers=headers, json=json, data=data, files=files
                )
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                raise EdubaoTransportError(f"Cannot connect to Edubao: {exc}", retryable=True) from exc
            except httpx.TransportError as exc:
                # The request may have been received (e.g. read timeout): don't blindly resend.
                raise EdubaoTransportError(f"Edubao transport error: {exc}") from exc

            status = resp.status_code
            try:
                body = resp.json()
            except ValueError:
                body = None
            return self._parse(resp, body)
        except EdubaoError as exc:
            error = str(exc)
            raise
        finally:
            if self._recorder:
                await self._safe_record(
                    CallRecord(
                        account_id=account_id,
                        method=method,
                        endpoint=path,
                        status_code=status,
                        latency_ms=int((time.monotonic() - started) * 1000),
                        request_summary=sanitize({"json": json, "data": data, "files": list(files or [])}),
                        response_summary=sanitize(body),
                        error=error,
                    )
                )

    @staticmethod
    def _parse(resp: httpx.Response, body: Any) -> dict:
        message = body.get("message") if isinstance(body, dict) else None
        if resp.status_code in (401, 403):
            raise EdubaoAuthError(message or "Unauthorized", status_code=resp.status_code, body=body)
        if not resp.is_success:
            raise EdubaoAPIError(message or f"HTTP {resp.status_code}", status_code=resp.status_code, body=body)
        if not isinstance(body, dict):
            raise EdubaoAPIError("Edubao returned a non-JSON response", status_code=resp.status_code)
        if body.get("status") is False:
            raise EdubaoAPIError(message or "Edubao reported failure", status_code=resp.status_code, body=body)
        return body

    async def _safe_record(self, record: CallRecord) -> None:
        try:
            await self._recorder(record)  # type: ignore[misc]
        except Exception:  # logging must never break an API call
            pass
