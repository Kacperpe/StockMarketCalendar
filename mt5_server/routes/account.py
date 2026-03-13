from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

import broker_state
import ct_client
from auth import require_api_key
from poller import get_snapshot

router = APIRouter(tags=["account"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/account", dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
def account(request: Request):
    use_ct = broker_state.is_ct() or ct_client.is_connected()
    if use_ct:
        snap = ct_client.get_snapshot()
    else:
        snap = get_snapshot()
    return snap.get("account") or {"error": "no data"}
