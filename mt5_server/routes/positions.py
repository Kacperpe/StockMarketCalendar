from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

import broker_state
import ct_client
from auth import require_api_key
from poller import get_snapshot

router = APIRouter(tags=["positions"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/positions", dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
def positions(request: Request):
    if broker_state.is_ct():
        snap = ct_client.get_snapshot()
    else:
        snap = get_snapshot()
    return snap.get("positions", [])
