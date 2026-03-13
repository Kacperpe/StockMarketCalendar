from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

import broker_state
import ct_client
from auth import require_api_key
from data_parser import compute_full_stats, parse_statistics

router = APIRouter(tags=["statistics"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/statistics", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
async def statistics(request: Request, days: int = 30):
    use_ct = broker_state.is_ct() or ct_client.is_connected()
    if use_ct:
        from ct_poller import get_ct_deals_async
        from ct_data_parser import parse_ct_statistics
        import ct_client as _cc
        deals = await get_ct_deals_async(days)
        sym_map = dict(_cc._symbol_map)
        return parse_ct_statistics(deals, days, sym_map)
    return parse_statistics(days)


@router.get("/statistics/full", dependencies=[Depends(require_api_key)])
@limiter.limit("6/minute")
async def statistics_full(request: Request, days: int = 30):
    """Kompletne statystyki w stylu Myfxbook."""
    use_ct = broker_state.is_ct() or ct_client.is_connected()
    if use_ct:
        from ct_poller import get_ct_deals_async
        from ct_data_parser import compute_ct_full_stats
        import ct_client as _cc
        deals  = await get_ct_deals_async(days)
        snap   = _cc.get_snapshot()
        acct   = snap.get("account") or {}
        sym_map = dict(_cc._symbol_map)
        return compute_ct_full_stats(
            deals,
            balance_start = acct.get("balance", 0),
            balance_end   = acct.get("balance", 0),
            currency      = acct.get("currency", ""),
            days          = days,
            symbol_map    = sym_map,
        )
    return compute_full_stats(days)
