"""
cTrader Open API client.

Runs a persistent Twisted reactor in a daemon background thread.
All cTrader requests are dispatched via reactor.callFromThread().
Thread-safe results are readable via get_snapshot() / get_equity_history().

Connection lifecycle
────────────────────
connect(…)   → starts reactor if needed → authenticates → starts polling
disconnect() → unsubscribes spots, sends ProtoOAAccountLogoutReq, stops poll
"""

import logging
import time
import threading
from collections import deque
from datetime import datetime
from threading import Lock, Event
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ── Shared state (protected by _lock) ────────────────────────────────────────
_lock = Lock()
_snapshot: Dict[str, Any] = {}
_equity_history: deque = deque(maxlen=500)
_symbol_map: Dict[int, str] = {}         # symbolId → name
_spot_prices: Dict[int, Dict] = {}       # symbolId → {bid, ask}
_positions_raw: list = []                # list of ProtoOAPosition objects

# Connection state
_connected   = False
_error: Optional[str] = None
_client      = None
_account_id: Optional[int] = None
_poll_handle = None                      # Twisted IDelayedCall

# Reactor thread (singleton — reactor can only run once per process)
_reactor_started = False
_reactor_lock    = threading.Lock()

POLL_INTERVAL = 5  # seconds between data refreshes


# ── Reactor ───────────────────────────────────────────────────────────────────

def _ensure_reactor():
    global _reactor_started
    with _reactor_lock:
        if _reactor_started:
            return
        _reactor_started = True

    def _run():
        # Import reactor *inside* the thread so it binds to this thread
        from twisted.internet import reactor as _reactor
        if not _reactor.running:
            _reactor.run(installSignalHandlers=False)

    t = threading.Thread(target=_run, daemon=True, name="ctrader-reactor")
    t.start()
    time.sleep(0.35)  # give reactor enough time to start its select loop


# ── Public API ────────────────────────────────────────────────────────────────

def connect(client_id: str, client_secret: str,
            access_token: str, account_id: int) -> tuple[bool, Optional[str]]:
    """
    Authenticate with cTrader.
    Returns (True, None) on success, (False, error_message) on failure.
    """
    global _account_id, _client, _connected, _error

    _ensure_reactor()

    _account_id = account_id

    auth_event  = Event()
    auth_result = {"ok": False, "error": None}

    def _do_connect():
        """Runs inside the Twisted thread."""
        global _client

        try:
            from twisted.internet import reactor
            from ctrader_open_api import Client, TcpProtocol, EndPoints
            from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import ProtoOAErrorRes
            from ctrader_open_api.messages.OpenApiMessages_pb2 import (
                ProtoOAApplicationAuthReq, ProtoOAApplicationAuthRes,
                ProtoOAAccountAuthReq,     ProtoOAAccountAuthRes,
                ProtoOASymbolsListReq,     ProtoOASymbolsListRes,
                ProtoOAReconcileReq,       ProtoOAReconcileRes,
                ProtoOATraderReq,          ProtoOATraderRes,
                ProtoOASubscribeSpotsReq,
                ProtoOASpotEvent,
                ProtoOADealListRes,
            )
            from ctrader_open_api import Protobuf

            # Stop previous client if any
            if _client is not None:
                try:
                    _client.stopService()
                except Exception:
                    pass
                _client = None

            client = Client(EndPoints.PROTRADE_HOST, EndPoints.PROTRADE_PORT, TcpProtocol)

            # ── Step 1: App auth ─────────────────────────────────────────────
            def on_connected(client):
                req             = ProtoOAApplicationAuthReq()
                req.clientId    = client_id
                req.clientSecret = client_secret
                client.send(req)

            def on_disconnected(client, reason):
                global _connected
                logger.warning(f"cTrader disconnected: {reason}")
                with _lock:
                    _connected = False

            # ── Step 2: Account auth ────────────────────────────────────────
            def on_app_auth_res(client, message):
                req = ProtoOAAccountAuthReq()
                req.ctidTraderAccountId = account_id
                req.accessToken         = access_token
                client.send(req)

            # ── Step 3: Request symbol list ─────────────────────────────────
            def on_account_auth_res(client, message):
                req = ProtoOASymbolsListReq()
                req.ctidTraderAccountId        = account_id
                req.includeArchivedSymbols     = False
                client.send(req)

            # ── Step 4: Cache symbols → start polling ───────────────────────
            def on_symbols_list(client, message):
                msg = Protobuf.extract(message)
                with _lock:
                    for sym in msg.symbol:
                        _symbol_map[sym.symbolId] = sym.symbolName

                auth_result["ok"] = True
                auth_event.set()
                # Start the polling loop
                _schedule_poll(client, account_id)

            # ── Error handler ────────────────────────────────────────────────
            def on_error(client, message):
                msg = Protobuf.extract(message)
                err = getattr(msg, "description", "Unknown cTrader error")
                logger.error(f"cTrader error: {err}")
                auth_result["error"] = err
                auth_event.set()

            # ── Spot price events ────────────────────────────────────────────
            def on_spot_event(client, message):
                msg = Protobuf.extract(message)
                with _lock:
                    entry = _spot_prices.get(msg.symbolId, {})
                    if msg.HasField("bid"):
                        entry["bid"] = msg.bid / 100000
                    if msg.HasField("ask"):
                        entry["ask"] = msg.ask / 100000
                    _spot_prices[msg.symbolId] = entry

            # ── Account info response ────────────────────────────────────────
            def on_trader_res(client, message):
                from ct_data_parser import parse_ct_account
                msg     = Protobuf.extract(message)
                trader  = msg.trader
                with _lock:
                    positions = list(_positions_raw)
                acct = parse_ct_account(trader, positions, _spot_prices)
                with _lock:
                    _snapshot["account"]   = acct
                    _snapshot["timestamp"] = datetime.utcnow().isoformat()
                    _equity_history.append({
                        "ts":      datetime.utcnow().isoformat(),
                        "equity":  acct.get("equity", acct.get("balance", 0)),
                        "balance": acct.get("balance", 0),
                        "pnl":     acct.get("floating_pnl", 0),
                    })

            # ── Reconcile (open positions) response ──────────────────────────
            def on_reconcile_res(client, message):
                from ct_data_parser import parse_ct_positions
                msg = Protobuf.extract(message)
                raw = list(msg.position)

                # Subscribe to spots for all open symbols
                sym_ids = list({p.tradeData.symbolId for p in raw})
                if sym_ids:
                    req = ProtoOASubscribeSpotsReq()
                    req.ctidTraderAccountId = account_id
                    for sid in sym_ids:
                        req.symbolId.append(sid)
                    client.send(req)

                parsed = parse_ct_positions(raw, _symbol_map, _spot_prices)
                with _lock:
                    _positions_raw[:] = raw
                    _snapshot["positions"] = parsed

            # ── Deal list response (correlated by clientMsgId) ───────────────
            def on_deal_list_res(client, message):
                msg     = Protobuf.extract(message)
                corr_id = message.clientMsgId
                if corr_id in _deal_pending:
                    _deal_pending[corr_id]["deals"].extend(list(msg.deal))
                    if not msg.hasMore:
                        _deal_pending[corr_id]["event"].set()

            # ── Register all callbacks ────────────────────────────────────────
            callbacks = {
                ProtoOAApplicationAuthRes().payloadType: on_app_auth_res,
                ProtoOAAccountAuthRes().payloadType:     on_account_auth_res,
                ProtoOASymbolsListRes().payloadType:     on_symbols_list,
                ProtoOATraderRes().payloadType:          on_trader_res,
                ProtoOAReconcileRes().payloadType:       on_reconcile_res,
                ProtoOASpotEvent().payloadType:          on_spot_event,
                ProtoOADealListRes().payloadType:        on_deal_list_res,
                ProtoOAErrorRes().payloadType:           on_error,
            }
            client.setConnectedCallback(on_connected)
            client.setDisconnectedCallback(on_disconnected)
            client.setMessageReceivedCallbacks(callbacks)
            client.startService()
            _client = client

        except Exception as exc:
            logger.exception("cTrader _do_connect failed")
            auth_result["error"] = str(exc)
            auth_event.set()

    from twisted.internet import reactor
    reactor.callFromThread(_do_connect)

    auth_event.wait(timeout=20.0)

    if auth_result["ok"]:
        with _lock:
            _connected = True
            _error     = None
        return True, None

    err = auth_result["error"] or "Connection timeout (20 s)"
    with _lock:
        _connected = False
        _error     = err
    return False, err


def disconnect():
    global _connected, _client, _poll_handle
    with _lock:
        _connected = False
    if _poll_handle is not None:
        try:
            from twisted.internet import reactor
            reactor.callFromThread(_poll_handle.cancel)
        except Exception:
            pass
        _poll_handle = None
    if _client is not None:
        try:
            from twisted.internet import reactor
            reactor.callFromThread(_client.stopService)
        except Exception:
            pass
        _client = None


def is_connected() -> bool:
    with _lock:
        return _connected


def get_snapshot() -> Dict[str, Any]:
    with _lock:
        return dict(_snapshot)


def get_equity_history() -> list:
    with _lock:
        return list(_equity_history)


# ── Deal list fetcher ─────────────────────────────────────────────────────────

_deal_pending: Dict[str, Any] = {}   # corr_id → {"event": Event, "deals": list}


def fetch_deals(from_ts_ms: int, to_ts_ms: int, max_rows: int = 10000) -> list:
    """
    Blocking call — fetches closed deals from cTrader for the given time range.
    Returns list of ProtoOADeal objects. Must NOT be called from the Twisted thread.
    """
    import uuid
    if not _connected or _client is None:
        return []

    corr_id = uuid.uuid4().hex
    ev      = Event()
    _deal_pending[corr_id] = {"event": ev, "deals": []}

    def _send():
        try:
            from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOADealListReq
            req = ProtoOADealListReq()
            req.ctidTraderAccountId = _account_id
            req.fromTimestamp       = from_ts_ms
            req.toTimestamp         = to_ts_ms
            req.maxRows             = max_rows
            _client.send(req, clientMsgId=corr_id)
        except Exception as exc:
            logger.error(f"CT fetch_deals send error: {exc}")
            _deal_pending.pop(corr_id, None)
            ev.set()

    from twisted.internet import reactor
    reactor.callFromThread(_send)
    ev.wait(timeout=30.0)
    return _deal_pending.pop(corr_id, {}).get("deals", [])


# ── Internal polling ──────────────────────────────────────────────────────────

def _schedule_poll(client, account_id: int):
    """Start or reschedule the periodic poll — must be called from Twisted thread."""
    from twisted.internet import reactor
    reactor.callLater(0, _poll_once, client, account_id)


def _poll_once(client, account_id: int):
    """Runs inside Twisted thread every POLL_INTERVAL seconds."""
    global _poll_handle
    if client is None or not _connected:
        return

    try:
        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOATraderReq, ProtoOAReconcileReq,
        )
        req1 = ProtoOATraderReq()
        req1.ctidTraderAccountId = account_id
        client.send(req1)

        req2 = ProtoOAReconcileReq()
        req2.ctidTraderAccountId = account_id
        client.send(req2)
    except Exception as exc:
        logger.error(f"CT poll error: {exc}")

    # Schedule next poll
    from twisted.internet import reactor
    _poll_handle = reactor.callLater(POLL_INTERVAL, _poll_once, client, account_id)
