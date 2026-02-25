import json
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.account_credential import AccountCredential
from app.models.broker_account import BrokerAccount
from app.models.enums import AccountStatus, BrokerProvider
from app.models.user import User
from app.schemas.accounts import (
    AccountCreate,
    AccountOut,
    CTraderConnectResponse,
    MT5ConnectResponse,
)


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def list_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[BrokerAccount]:
    return list(
        db.scalars(
            select(BrokerAccount).where(BrokerAccount.user_id == current_user.id).order_by(BrokerAccount.created_at.desc())
        )
    )


@router.post("", response_model=AccountOut, status_code=201)
def create_account(
    payload: AccountCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> BrokerAccount:
    account = BrokerAccount(
        user_id=current_user.id,
        provider=payload.provider,
        name=payload.name,
        currency=payload.currency.upper(),
        status=AccountStatus.NEW,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountOut)
def get_account(
    account_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> BrokerAccount:
    account = db.scalar(
        select(BrokerAccount).where(BrokerAccount.id == account_id, BrokerAccount.user_id == current_user.id)
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/{account_id}/connect/mt5", response_model=MT5ConnectResponse)
def connect_mt5(
    account_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MT5ConnectResponse:
    account = db.scalar(
        select(BrokerAccount).where(BrokerAccount.id == account_id, BrokerAccount.user_id == current_user.id)
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.provider != BrokerProvider.MT5:
        raise HTTPException(status_code=400, detail="Account provider is not MT5")

    ingest_key = secrets.token_urlsafe(32)
    payload = {"ingest_key": ingest_key, "version": 1}
    if account.credentials:
        account.credentials.encrypted_payload = json.dumps(payload).encode("utf-8")
    else:
        db.add(AccountCredential(account_id=account.id, encrypted_payload=json.dumps(payload).encode("utf-8")))

    account.status = AccountStatus.ACTIVE
    db.commit()

    return MT5ConnectResponse(
        account_id=account.id,
        ingest_key=ingest_key,
        api_url="/api/ingest/mt5/snapshot",
        instructions=[
            "Skonfiguruj EA: API_URL, ACCOUNT_ID, INGEST_KEY, SYNC_INTERVAL_SEC.",
            "Podpisuj payload HMAC w naglowkach X-Signature, X-Timestamp, X-Nonce.",
            "Wysylaj account_state, deals i positions cyklicznie (idempotencja po provider_trade_id).",
        ],
    )


@router.post("/{account_id}/connect/ctrader", response_model=CTraderConnectResponse)
def connect_ctrader(
    account_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CTraderConnectResponse:
    account = db.scalar(
        select(BrokerAccount).where(BrokerAccount.id == account_id, BrokerAccount.user_id == current_user.id)
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.provider != BrokerProvider.CTRADER:
        raise HTTPException(status_code=400, detail="Account provider is not CTrader")

    state = secrets.token_urlsafe(24)
    oauth_query = urlencode({"state": state, "account_id": account.id, "response_type": "code"})
    return CTraderConnectResponse(
        account_id=account.id,
        oauth_url=f"https://connect.spotware.com/apps/auth?{oauth_query}",
        state=state,
        note="MVP placeholder: dodaj client_id, redirect_uri i token exchange po stronie backendu.",
    )

