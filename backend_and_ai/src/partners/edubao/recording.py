from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

_REDACT = {
    "password", "user_password", "otp", "client_secret", "x_api_key", "x-api-key",
    "access_token", "refresh_token", "authorization",
}


@dataclass
class CallRecord:
    account_id: int | None
    method: str
    endpoint: str
    status_code: int | None
    latency_ms: int
    request_summary: dict | None
    response_summary: Any
    error: str | None


CallRecorder = Callable[[CallRecord], Awaitable[None]]


def sanitize(value: Any) -> Any:
    """Redact secrets and drop file bytes so payloads are safe to store in the call log."""
    if isinstance(value, dict):
        return {k: "***" if str(k).lower() in _REDACT else sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, (bytes, bytearray)):
        return f"<{len(value)} bytes>"
    return value
