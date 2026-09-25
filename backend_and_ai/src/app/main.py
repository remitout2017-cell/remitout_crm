from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.auth import require_admin
from app.deps import init_edubao
from app.routers import lead_documents, leads, partners, reference, students
from core.security import EncryptionError
from partners.edubao.errors import EdubaoAPIError, EdubaoError, EdubaoRateLimitError
from services.leads import LeadNotFound, LeadValidationError, StepOrderError
from services.partner_onboarding import OnboardingError


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_edubao(app)
    yield
    await app.state.edubao_http.aclose()
    await app.state.cache.close()


app = FastAPI(title="Remitout CRM", lifespan=lifespan)

# Everything except /health requires the admin key.
_protected = [Depends(require_admin)]
app.include_router(students.router, dependencies=_protected)
app.include_router(partners.router, dependencies=_protected)
app.include_router(leads.router, dependencies=_protected)
app.include_router(lead_documents.router, dependencies=_protected)
app.include_router(reference.router, dependencies=_protected)


def _json(detail: str, status: int) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status)


@app.exception_handler(EdubaoRateLimitError)
async def edubao_rate_limited(_: Request, exc: EdubaoRateLimitError):
    resp = _json(f"Edubao: {exc}", 429)
    if exc.retry_after is not None:
        resp.headers["Retry-After"] = str(exc.retry_after)
    return resp


@app.exception_handler(EdubaoError)
async def edubao_error(_: Request, exc: EdubaoError):
    # Edubao rejected our input (e.g. bad password/OTP/payload) -> 400; anything else is upstream trouble -> 502.
    client_error = isinstance(exc, EdubaoAPIError) and 400 <= exc.status_code < 500
    return _json(f"Edubao: {exc}", 400 if client_error else 502)


@app.exception_handler(OnboardingError)
@app.exception_handler(LeadNotFound)
async def not_found(_: Request, exc: Exception):
    return _json(str(exc), 404)


@app.exception_handler(StepOrderError)
async def step_order(_: Request, exc: StepOrderError):
    return _json(str(exc), 409)


@app.exception_handler(LeadValidationError)
async def lead_validation(_: Request, exc: LeadValidationError):
    return _json(str(exc), 422)


@app.exception_handler(EncryptionError)
async def encryption_error(_: Request, exc: EncryptionError):
    return _json("Server encryption is misconfigured", 500)


@app.get("/health")
async def health():
    return {"status": "ok"}
