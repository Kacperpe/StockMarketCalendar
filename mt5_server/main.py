import asyncio
import importlib.util
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import MetaTrader5 as mt5
from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import broker_state


def _load_ctrader_support():
    missing_runtime = [
        module_name
        for module_name in ("twisted", "ctrader_open_api")
        if importlib.util.find_spec(module_name) is None
    ]
    if missing_runtime:
        missing = ", ".join(missing_runtime)
        return None, None, (
            "cTrader support is not installed. Missing Python packages: "
            f"{missing}. Install cTrader dependencies and restart the server: "
            "pip install -r mt5_server/requirements-ctrader.txt. "
            "MT5 mode works without cTrader packages."
        )

    try:
        import ct_client as loaded_ct_client
        import ct_oauth as loaded_ct_oauth
        return loaded_ct_client, loaded_ct_oauth, None
    except Exception as exc:
        return None, None, f"cTrader support failed to load: {exc}"
try:
    import ct_client
    import ct_oauth
    CT_AVAILABLE = True
except ImportError:
    ct_client = None  # type: ignore
    ct_oauth   = None  # type: ignore
    CT_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "ctrader-open-api not installed — cTrader support disabled. "
        "Install with: pip install ctrader-open-api"
    )
ct_client, ct_oauth, CT_ERROR = _load_ctrader_support()
CT_AVAILABLE = CT_ERROR is None

if CT_ERROR:
    logging.getLogger(__name__).warning(CT_ERROR)

from auth import clear_session, create_session, is_authenticated, require_api_key
from config import settings
from data_parser import build_full_equity_curve, get_overview_stats
from mt5_client import connect_dynamic, disconnect
from poller import get_equity_history, get_snapshot, polling_loop
from routes.account import router as account_router
from routes.calendar import router as calendar_router
from routes.positions import router as positions_router
from routes.stats import router as stats_router
from ws_manager import ws_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

_poller_task: Optional[asyncio.Task] = None

# OAuth2 state for cTrader (single-user tool — no multiuser needed)
_CT_REDIRECT_URI = "http://localhost:8000/auth/ctrader/callback"
_ct_oauth_pending: dict = {
    "client_id":     None,
    "client_secret": None,
    "access_token":  None,
}

# Persisted cTrader session (loaded from / saved to ct_session.json)
_CT_SESSION_PATH = Path(__file__).resolve().parent / "ct_session.json"
_ct_saved_session: dict = {}   # populated by _load_ct_session()


def _load_ct_session() -> None:
    """Load persisted cTrader credentials into memory on startup."""
    global _ct_saved_session
    try:
        if _CT_SESSION_PATH.exists():
            import json
            data = json.loads(_CT_SESSION_PATH.read_text(encoding="utf-8"))
            _ct_saved_session = data
            # Pre-populate oauth pending so reconnect works without re-auth
            _ct_oauth_pending["client_id"]    = data.get("client_id")
            _ct_oauth_pending["client_secret"] = data.get("client_secret")
            _ct_oauth_pending["access_token"] = data.get("access_token")
            logger.info(
                "Loaded saved cTrader session for account %s", data.get("account_id")
            )
    except Exception as exc:
        logger.warning("Could not load saved cTrader session: %s", exc)


def _save_ct_session(
    client_id: str,
    client_secret: str,
    access_token: str,
    account_id: int,
    is_live: bool,
    account_name: str,
) -> None:
    """Persist cTrader credentials to disk for future auto-reconnect."""
    global _ct_saved_session
    import json
    from datetime import timezone
    data = {
        "client_id":    client_id,
        "client_secret": client_secret,
        "access_token": access_token,
        "account_id":   account_id,
        "is_live":      is_live,
        "account_name": account_name,
        "saved_at":     datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
    }
    try:
        _CT_SESSION_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        _ct_saved_session = data
        logger.info("Saved cTrader session to %s", _CT_SESSION_PATH)
    except Exception as exc:
        logger.warning("Could not save cTrader session: %s", exc)


def _clear_ct_session() -> None:
    """Remove persisted cTrader session from disk."""
    global _ct_saved_session
    _ct_saved_session = {}
    try:
        if _CT_SESSION_PATH.exists():
            _CT_SESSION_PATH.unlink()
    except Exception as exc:
        logger.warning("Could not remove cTrader session file: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optionally pre-initialise MT5 terminal — disabled by default so that
    # cTrader-only users do not see MT5 launch on startup.
    if settings.AUTO_INIT_MT5:
        try:
            mt5.initialize()
            logger.info("MT5 terminal initialized — waiting for user login via browser")
        except Exception:
            logger.info("MT5 not available — cTrader-only mode")
    else:
        logger.info("MT5 auto-init disabled (AUTO_INIT_MT5=False) — connect via browser login")

    # Try to restore a saved cTrader session so users don't need to re-authorise
    _load_ct_session()

    yield
    global _poller_task
    if _poller_task and not _poller_task.done():
        _poller_task.cancel()
    disconnect()
    if CT_AVAILABLE and ct_client:
        ct_client.disconnect()


app = FastAPI(title="MT5 Monitor", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

_static = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=_static), name="static")

_VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"


def _read_version() -> str:
    try:
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


@app.get("/")
def root():
    return FileResponse(_static / "index.html")


@app.get("/version")
def version_endpoint():
    return {"version": _read_version()}


# ── Auth ──────────────────────────────────────────────────────────────────────

class ConnectRequest(BaseModel):
    login: int
    server: str
    password: str


@app.post("/auth/connect")
async def auth_connect(req: ConnectRequest):
    global _poller_task

    if not connect_dynamic(req.login, req.password, req.server):
        return {
            "ok": False,
            "error": (
                "Nie można połączyć z MT5. "
                "Sprawdź login, serwer, hasło oraz czy terminal MT5 jest uruchomiony."
            ),
        }

    token = create_session()

    # Uruchom (lub zrestartuj) pętlę pollingu
    if _poller_task and not _poller_task.done():
        _poller_task.cancel()
    _poller_task = asyncio.create_task(polling_loop(ws_manager))

    info = mt5.account_info()
    return {
        "ok":       True,
        "token":    token,
        "name":     info.name     if info else "",
        "server":   info.server   if info else req.server,
        "currency": info.currency if info else "",
    }


@app.post("/auth/logout")
def auth_logout():
    global _poller_task
    if _poller_task and not _poller_task.done():
        _poller_task.cancel()
        _poller_task = None
    clear_session()
    if broker_state.is_mt5():
        disconnect()
    else:
        if CT_AVAILABLE and ct_client:
            ct_client.disconnect()
    broker_state.set_broker(broker_state.BROKER_MT5)  # reset to default
    return {"ok": True}


# ── cTrader OAuth2 & connect ─────────────────────────────────────────────────

class CTAuthorizeRequest(BaseModel):
    client_id:     str
    client_secret: str


class CTConnectRequest(BaseModel):
    account_id: int
    is_live: bool = False


@app.post("/auth/ctrader/authorize")
def ct_authorize(req: CTAuthorizeRequest):
    """Store credentials and return the Spotware OAuth2 authorization URL."""
    if not CT_AVAILABLE:
        return {"ok": False, "error": CT_ERROR}
    _ct_oauth_pending["client_id"]     = req.client_id
    _ct_oauth_pending["client_secret"] = req.client_secret
    _ct_oauth_pending["access_token"]  = None
    url = ct_oauth.get_auth_url(req.client_id, _CT_REDIRECT_URI)
    return {"ok": True, "auth_url": url}


@app.get("/auth/ctrader/callback")
def ct_callback(code: str = None, error: str = None):
    """OAuth2 redirect target — exchanges code for access token."""
    if error:
        return HTMLResponse(
            f"<html><body style='font-family:sans-serif;padding:40px'>"
            f"<h2>❌ Błąd autoryzacji</h2><p>{error}</p>"
            f"<p>Zamknij to okno.</p></body></html>"
        )
    if not code or not _ct_oauth_pending.get("client_id"):
        return HTMLResponse(
            "<html><body style='font-family:sans-serif;padding:40px'>"
            "<h2>⚠️ Nieprawidłowe żądanie</h2><p>Zamknij to okno.</p></body></html>"
        )

    token, err = ct_oauth.exchange_code(
        code,
        _ct_oauth_pending["client_id"],
        _ct_oauth_pending["client_secret"],
        _CT_REDIRECT_URI,
    )
    if err:
        return HTMLResponse(
            f"<html><body style='font-family:sans-serif;padding:40px'>"
            f"<h2>❌ Błąd wymiany tokenu</h2><p>{err}</p>"
            f"<p>Zamknij to okno i spróbuj ponownie.</p></body></html>"
        )

    _ct_oauth_pending["access_token"] = token
    return HTMLResponse(
        "<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
        "<h2>✅ Autoryzacja zakończona pomyślnie!</h2>"
        "<p>Możesz zamknąć to okno i wrócić do dashboardu.</p>"
        "<script>setTimeout(() => window.close(), 2000)</script>"
        "</body></html>"
    )


@app.get("/auth/ctrader/token-status")
def ct_token_status():
    """Frontend polls this until access_token is available after OAuth popup."""
    return {"ready": bool(_ct_oauth_pending.get("access_token"))}


@app.get("/auth/ctrader/accounts", dependencies=[Depends(require_api_key)])
def ct_accounts_list(request: Request):
    token = _ct_oauth_pending.get("access_token")
    if not token:
        return {"ok": False, "error": "No access token — authorize first"}
    accounts, err = ct_client.get_accounts_by_token(
        token,
        _ct_oauth_pending["client_id"],
        _ct_oauth_pending["client_secret"],
    )
    if err:
        return {"ok": False, "error": err}
    return {"ok": True, "accounts": accounts}


@app.get("/auth/ctrader/accounts-pre")
def ct_accounts_list_pre():
    """List accounts BEFORE session exists (after OAuth callback, before connect)."""
    token = _ct_oauth_pending.get("access_token")
    if not token:
        return {"ok": False, "error": "No access token"}
    accounts, err = ct_client.get_accounts_by_token(
        token,
        _ct_oauth_pending["client_id"],
        _ct_oauth_pending["client_secret"],
    )
    if err:
        return {"ok": False, "error": err}
    return {"ok": True, "accounts": accounts}


@app.post("/auth/ctrader/connect")
async def ct_connect(req: CTConnectRequest):
    if not CT_AVAILABLE:
        return {"ok": False, "error": CT_ERROR}
    global _poller_task

    token = _ct_oauth_pending.get("access_token")
    if not token:
        return {"ok": False, "error": "No access token — authorize first"}

    client_id     = _ct_oauth_pending["client_id"]
    client_secret = _ct_oauth_pending["client_secret"]

    # connect() is blocking (Twisted) — run in thread pool
    loop = asyncio.get_event_loop()
    ok, err = await loop.run_in_executor(
        None, ct_client.connect, client_id, client_secret, token, req.account_id, req.is_live
    )
    if not ok:
        return {"ok": False, "error": err}

    broker_state.set_broker(broker_state.BROKER_CT)

    # Stop MT5 poller if running
    if _poller_task and not _poller_task.done():
        _poller_task.cancel()
        _poller_task = None

    session_token = create_session()
    snap = ct_client.get_snapshot()
    acct = snap.get("account") or {}
    account_name = str(acct.get("login", req.account_id))

    # Persist credentials so the user can reconnect without re-authorising
    _save_ct_session(
        client_id, client_secret, token,
        req.account_id, req.is_live, account_name,
    )

    return {
        "ok":       True,
        "token":    session_token,
        "name":     account_name,
        "server":   acct.get("server", "cTrader"),
        "currency": acct.get("currency", ""),
        "broker":   "ctrader",
    }


@app.get("/auth/ctrader/saved-session")
def ct_saved_session():
    """Return non-sensitive info about the persisted cTrader session (if any)."""
    if not _ct_saved_session:
        return {"available": False}
    return {
        "available":    True,
        "account_id":   _ct_saved_session.get("account_id"),
        "account_name": _ct_saved_session.get("account_name"),
        "is_live":      _ct_saved_session.get("is_live", False),
        "saved_at":     _ct_saved_session.get("saved_at"),
    }


@app.post("/auth/ctrader/reconnect")
async def ct_reconnect():
    """Reconnect using the persisted cTrader session without re-authorising."""
    if not CT_AVAILABLE:
        return {"ok": False, "error": CT_ERROR}
    if not _ct_saved_session:
        return {"ok": False, "error": "No saved session — authorise first"}

    global _poller_task

    client_id     = _ct_saved_session["client_id"]
    client_secret = _ct_saved_session["client_secret"]
    access_token  = _ct_saved_session["access_token"]
    account_id    = _ct_saved_session["account_id"]
    is_live       = _ct_saved_session.get("is_live", False)

    # Restore into pending so other helpers that read it keep working
    _ct_oauth_pending["client_id"]    = client_id
    _ct_oauth_pending["client_secret"] = client_secret
    _ct_oauth_pending["access_token"] = access_token

    loop = asyncio.get_event_loop()
    ok, err = await loop.run_in_executor(
        None, ct_client.connect, client_id, client_secret, access_token, account_id, is_live
    )
    if not ok:
        # Token may have expired — clear saved session so user can re-auth
        _clear_ct_session()
        return {"ok": False, "error": f"Zapisana sesja wygasła lub jest nieprawidłowa: {err}"}

    broker_state.set_broker(broker_state.BROKER_CT)

    if _poller_task and not _poller_task.done():
        _poller_task.cancel()
        _poller_task = None

    session_token = create_session()
    snap = ct_client.get_snapshot()
    acct = snap.get("account") or {}
    account_name = str(acct.get("login", account_id))

    # Refresh saved session with latest account name
    _save_ct_session(client_id, client_secret, access_token, account_id, is_live, account_name)

    return {
        "ok":       True,
        "token":    session_token,
        "name":     account_name,
        "server":   acct.get("server", "cTrader"),
        "currency": acct.get("currency", ""),
        "broker":   "ctrader",
    }


# ── REST ──────────────────────────────────────────────────────────────────────

app.include_router(account_router)
app.include_router(calendar_router)
app.include_router(positions_router)
app.include_router(stats_router)


@app.get("/snapshot", dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
def snapshot_endpoint(request: Request):
    if broker_state.is_ct():
        return ct_client.get_snapshot()
    return get_snapshot()


@app.get("/history", dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
def history_endpoint(request: Request):
    if broker_state.is_ct():
        return ct_client.get_equity_history()
    return get_equity_history()


@app.get("/overview", dependencies=[Depends(require_api_key)])
@limiter.limit("15/minute")
async def overview_endpoint(request: Request):
    if broker_state.is_ct():
        from ct_poller import get_ct_all_deals_async
        from ct_data_parser import compute_ct_overview
        snap  = ct_client.get_snapshot()
        acct  = snap.get("account") or {}
        deals = await get_ct_all_deals_async()
        return compute_ct_overview(
            deals,
            acct.get("balance", 0),
            acct.get("currency", ""),
        )
    return get_overview_stats()


@app.get("/equity-curve", dependencies=[Depends(require_api_key)])
@limiter.limit("6/minute")
async def equity_curve_endpoint(request: Request):
    if broker_state.is_ct():
        from ct_poller import get_ct_all_deals_async
        from ct_data_parser import compute_ct_equity_curve
        deals = await get_ct_all_deals_async()
        return compute_ct_equity_curve(deals)
    return build_full_equity_curve()


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    key = websocket.query_params.get("key")
    if not is_authenticated(key):
        await websocket.close(code=4001)
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
