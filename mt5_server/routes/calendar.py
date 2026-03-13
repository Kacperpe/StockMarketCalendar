from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from auth import require_api_key
from data_calendar import get_calendar_data
from datetime import datetime

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/calendar", dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
async def calendar_endpoint(request: Request, year: int = None, month: int = None):
    import broker_state
    import ct_client as _cc
    now = datetime.utcnow()
    y = year  if year  is not None else now.year
    m = month if month is not None else now.month

    if broker_state.is_ct() or _cc.is_connected():
        from ct_poller import get_ct_deals_async
        from ct_data_parser import compute_ct_calendar
        # Fetch only the relevant month from cTrader
        from datetime import timedelta
        month_start = datetime(y, m, 1)
        month_end   = datetime(y + 1, 1, 1) if m == 12 else datetime(y, m + 1, 1)
        from_ms = int(month_start.timestamp() * 1000)
        to_ms   = int(month_end.timestamp()   * 1000)
        import asyncio
        loop  = asyncio.get_event_loop()
        deals = await loop.run_in_executor(
            None, _cc.fetch_deals, from_ms, to_ms
        )
        sym_map = dict(_cc._symbol_map)
        return compute_ct_calendar(deals, y, m, sym_map)

    return get_calendar_data(y, m)
