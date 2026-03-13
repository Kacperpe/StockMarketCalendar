"""
Async helpers for cTrader data fetching (runs blocking CT calls in executor).
"""

import asyncio
from datetime import datetime, timedelta

_CASHFLOW_CACHE_TTL_SEC = 300
_cashflow_cache_items: list = []
_cashflow_cache_ts: float = 0.0

async def get_ct_deals_async(days: int) -> list:
    """
    Fetch CT deal history for `days` days, non-blocking for FastAPI.
    Returns list of ProtoOADeal objects.
    """
    import ct_client
    if not ct_client.is_connected():
        return []

    now      = datetime.utcnow()
    since    = now - timedelta(days=days) if days > 0 else datetime(2000, 1, 1)
    from_ms  = int(since.timestamp() * 1000)
    to_ms    = int(now.timestamp()   * 1000)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, ct_client.fetch_deals, from_ms, to_ms
    )


async def get_ct_all_deals_async() -> list:
    """Fetch complete deal history (for equity curve / overview)."""
    import ct_client
    if not ct_client.is_connected():
        return []

    from_ms = int(datetime(2000, 1, 1).timestamp() * 1000)
    to_ms   = int(datetime.utcnow().timestamp()    * 1000)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, ct_client.fetch_deals, from_ms, to_ms
    )


async def get_ct_all_cash_flows_async() -> list:
    """Fetch complete deposit/withdraw history for cTrader overview."""
    import ct_client
    import time
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
