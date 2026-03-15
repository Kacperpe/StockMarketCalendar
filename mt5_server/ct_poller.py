"""
Async helpers for cTrader data fetching (runs blocking CT calls in executor).

Deals and cash-flow results are cached for _*_CACHE_TTL_SEC seconds so that
concurrent requests (e.g. /overview + /equity-curve firing at the same time)
share a single fetch instead of each sending their own 300+ chunk request.
"""

import asyncio
import time
from datetime import datetime, timedelta

_CASHFLOW_CACHE_TTL_SEC = 300
_DEALS_CACHE_TTL_SEC = 300

# ── cash-flow cache ───────────────────────────────────────────────────────────
_cashflow_cache_items: list = []
_cashflow_cache_ts: float = 0.0

# ── all-deals cache (used by /overview and /equity-curve) ────────────────────
_all_deals_cache_items: list = []
_all_deals_cache_ts: float = 0.0
_all_deals_lock: "asyncio.Lock | None" = None

# ── per-days cache (used by /statistics and /statistics/full) ─────────────────
# maps days -> (fetched_at_ts, items_list)
_deals_by_days_cache: dict = {}
_deals_by_days_lock: "asyncio.Lock | None" = None


def _get_all_deals_lock() -> asyncio.Lock:
    global _all_deals_lock
    if _all_deals_lock is None:
        _all_deals_lock = asyncio.Lock()
    return _all_deals_lock


def _get_deals_by_days_lock() -> asyncio.Lock:
    global _deals_by_days_lock
    if _deals_by_days_lock is None:
        _deals_by_days_lock = asyncio.Lock()
    return _deals_by_days_lock


def clear_deals_cache() -> None:
    """
    Invalidate all cached deal data.  Call this whenever the active cTrader
    account changes so stale data is not returned to the next caller.
    """
    global _all_deals_cache_items, _all_deals_cache_ts, _deals_by_days_cache
    _all_deals_cache_items = []
    _all_deals_cache_ts = 0.0
    _deals_by_days_cache = {}


async def get_ct_deals_async(days: int) -> list:
    """
    Fetch CT deal history for `days` days, non-blocking for FastAPI.
    Results are cached for _DEALS_CACHE_TTL_SEC seconds.  Concurrent callers
    requesting the same `days` value will wait for the first fetch to complete
    and then receive the cached result, avoiding duplicate 300+ chunk requests.
    """
    import ct_client
    if not ct_client.is_connected():
        return []

    now_ts = time.time()
    cached = _deals_by_days_cache.get(days)
    if cached and now_ts - cached[0] < _DEALS_CACHE_TTL_SEC:
        return list(cached[1])

    async with _get_deals_by_days_lock():
        # Double-check after acquiring lock (another coroutine may have fetched)
        now_ts = time.time()
        cached = _deals_by_days_cache.get(days)
        if cached and now_ts - cached[0] < _DEALS_CACHE_TTL_SEC:
            return list(cached[1])

        now = datetime.utcnow()
        since = now - timedelta(days=days) if days > 0 else datetime(2000, 1, 1)
        from_ms = int(since.timestamp() * 1000)
        to_ms = int(now.timestamp() * 1000)

        loop = asyncio.get_event_loop()
        items = await loop.run_in_executor(None, ct_client.fetch_deals, from_ms, to_ms)
        _deals_by_days_cache[days] = (time.time(), list(items or []))
        return list(_deals_by_days_cache[days][1])


async def get_ct_all_deals_async() -> list:
    """
    Fetch complete deal history (for equity curve / overview).
    Results are cached for _DEALS_CACHE_TTL_SEC seconds.  Concurrent callers
    wait on a lock so only one network fetch happens at a time.
    """
    import ct_client
    if not ct_client.is_connected():
        return []

    global _all_deals_cache_items, _all_deals_cache_ts

    now_ts = time.time()
    if _all_deals_cache_items and now_ts - _all_deals_cache_ts < _DEALS_CACHE_TTL_SEC:
        return list(_all_deals_cache_items)

    async with _get_all_deals_lock():
        # Double-check after acquiring lock
        now_ts = time.time()
        if _all_deals_cache_items and now_ts - _all_deals_cache_ts < _DEALS_CACHE_TTL_SEC:
            return list(_all_deals_cache_items)

        from_ms = int(datetime(2000, 1, 1).timestamp() * 1000)
        to_ms = int(datetime.utcnow().timestamp() * 1000)

        loop = asyncio.get_event_loop()
        items = await loop.run_in_executor(None, ct_client.fetch_deals, from_ms, to_ms)
        _all_deals_cache_items = list(items or [])
        _all_deals_cache_ts = time.time()
        return list(_all_deals_cache_items)


async def get_ct_all_cash_flows_async() -> list:
    """Fetch complete deposit/withdraw history for cTrader overview."""
    import ct_client
    if not ct_client.is_connected():
        return []

    global _cashflow_cache_items, _cashflow_cache_ts
    now_ts = time.time()
    if _cashflow_cache_items and now_ts - _cashflow_cache_ts < _CASHFLOW_CACHE_TTL_SEC:
        return list(_cashflow_cache_items)

    from_ms = int(datetime(2000, 1, 1).timestamp() * 1000)
    to_ms = int(datetime.utcnow().timestamp() * 1000)

    loop = asyncio.get_event_loop()
    try:
        items = await loop.run_in_executor(
            None, ct_client.fetch_cash_flows, from_ms, to_ms
        )
        _cashflow_cache_items = list(items or [])
        _cashflow_cache_ts = now_ts
        return list(_cashflow_cache_items)
    except Exception:
        # Keep the previous cache if fetching fails.
        return list(_cashflow_cache_items)
