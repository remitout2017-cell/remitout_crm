from collections.abc import Callable

from fastapi import FastAPI, Request

from core.cache import Cache, keys, make_cache
from db.session import SessionLocal
from partners.edubao.auth import TokenManager
from partners.edubao.client import EdubaoPartnerClient
from partners.edubao.http import EdubaoHTTP
from partners.edubao.onboarding import EdubaoAuthAPI
from partners.edubao.store import DbTokenStore, db_call_recorder, db_password_provider


def init_edubao(app: FastAPI) -> None:
    """Build the process-wide Edubao objects. TokenManager must be a singleton (it holds the locks)."""
    http = EdubaoHTTP(recorder=db_call_recorder(SessionLocal))
    cache = make_cache()
    store = DbTokenStore(SessionLocal, on_change=lambda account_id: app.state.cache.delete(keys.partner(account_id)))
    app.state.cache = cache
    app.state.edubao_http = http
    app.state.edubao_store = store
    app.state.edubao_tokens = TokenManager(
        store,
        EdubaoAuthAPI(http),
        db_password_provider(SessionLocal),
        lock_factory=lambda name: app.state.cache.lock(name),
    )


def get_cache(request: Request) -> Cache:
    return request.app.state.cache


def get_edubao_http(request: Request) -> EdubaoHTTP:
    return request.app.state.edubao_http


def get_auth_api(request: Request) -> EdubaoAuthAPI:
    return EdubaoAuthAPI(request.app.state.edubao_http)


def get_client_factory(request: Request) -> Callable[[int], EdubaoPartnerClient]:
    st = request.app.state
    return lambda account_id: EdubaoPartnerClient(account_id, st.edubao_http, st.edubao_store, st.edubao_tokens)
