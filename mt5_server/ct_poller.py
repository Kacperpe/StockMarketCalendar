"""
Async helpers for cTrader data fetching (runs blocking CT calls in executor).
"""

import asyncio
from datetime import datetime, timedelta


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
