import hashlib
import hmac
import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.models.account_credential import AccountCredential
from app.models.broker_account import BrokerAccount
from app.models.daily_metric import DailyAccountMetric
from app.models.enums import TradeRecordType, TradeSide, TradeStatus
from app.models.trade import Trade
from app.schemas.ingest import MT5SnapshotRequest


router = APIRouter(prefix="/ingest/mt5", tags=["ingest"])


def _load_ingest_key(credential: AccountCredential) -> str:
    try:
        payload = json.loads(credential.encrypted_payload.decode("utf-8"))
        return payload["ingest_key"]
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Invalid account credential payload") from exc


def _verify_hmac(secret: str, body: bytes, signature: str, timestamp: str, nonce: str) -> bool:
    message = b".".join([timestamp.encode("utf-8"), nonce.encode("utf-8"), body])
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _coerce_trade_side(value: str) -> TradeSide:
    return TradeSide.BUY if value.lower() == "buy" else TradeSide.SELL


def _coerce_trade_status(value: str) -> TradeStatus:
    return TradeStatus.OPEN if value.lower() == "open" else TradeStatus.CLOSED


def _recompute_daily_metrics(db: Session, account_id: int) -> None:
    # MVP baseline: recompute only impacted days in future iteration. For now recompute all closed-trade daily rows.
    closed_trades = list(
        db.scalars(select(Trade).where(Trade.account_id == account_id, Trade.status == TradeStatus.CLOSED))
    )
    existing = list(db.scalars(select(DailyAccountMetric).where(DailyAccountMetric.account_id == account_id)))
    for row in existing:
        db.delete(row)

    tz = ZoneInfo(settings.app_timezone)
    grouped: dict = {}
    for trade in closed_trades:
        if not trade.close_time:
            continue
        d = trade.close_time.astimezone(tz).date()
        bucket = grouped.setdefault(
            d,
            {
                "realized_pnl": Decimal("0"),
                "commissions": Decimal("0"),
                "swaps": Decimal("0"),
                "fees": Decimal("0"),
                "net_pnl": Decimal("0"),
            },
        )
        pnl = Decimal(trade.pnl or 0)
        commission = Decimal(trade.commission or 0)
        swap = Decimal(trade.swap or 0)
        fees = Decimal(trade.fees or 0)
        bucket["realized_pnl"] += pnl
        bucket["commissions"] += commission
        bucket["swaps"] += swap
        bucket["fees"] += fees
        bucket["net_pnl"] += pnl - commission - swap - fees

    for d, values in grouped.items():
        db.add(DailyAccountMetric(account_id=account_id, date=d, **values))


@router.post("/snapshot", status_code=status.HTTP_202_ACCEPTED)
async def ingest_mt5_snapshot(
    request: Request,
    payload: MT5SnapshotRequest,
    x_signature: str = Header(alias="X-Signature"),
    x_timestamp: str = Header(alias="X-Timestamp"),
    x_nonce: str = Header(alias="X-Nonce"),
    db: Session = Depends(get_db),
):
    account = db.scalar(select(BrokerAccount).where(BrokerAccount.id == payload.account_id))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    credential = db.scalar(select(AccountCredential).where(AccountCredential.account_id == payload.account_id))
    if not credential:
        raise HTTPException(status_code=401, detail="Missing ingest credentials")

    body = await request.body()
    ingest_key = _load_ingest_key(credential)
    if not _verify_hmac(ingest_key, body, x_signature, x_timestamp, x_nonce):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        ts = datetime.fromisoformat(x_timestamp.replace("Z", "+00:00"))
        if abs((datetime.now(UTC) - ts.astimezone(UTC)).total_seconds()) > 300:
            raise HTTPException(status_code=401, detail="Timestamp outside replay window")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Timestamp format") from None

    for deal in payload.deals:
        values = {
            "id": str(uuid4()),
            "account_id": payload.account_id,
            "provider_trade_id": deal.provider_trade_id,
            "symbol": deal.symbol,
            "side": _coerce_trade_side(deal.side).value,
            "volume": deal.volume,
            "open_time": deal.open_time,
            "close_time": deal.close_time,
            "open_price": deal.open_price,
            "close_price": deal.close_price,
            "commission": deal.commission,
            "swap": deal.swap,
            "fees": deal.fees,
            "pnl": deal.pnl,
            "status": _coerce_trade_status(deal.status).value,
            "record_type": TradeRecordType.DEAL.value,
            "magic": deal.magic,
            "comment": deal.comment,
            "raw_json": deal.raw_json,
        }
        values = {k: v for k, v in values.items() if v is not None}
        stmt = pg_insert(Trade).values(**values)
        update_cols = {
            "id": Trade.id,
            "symbol": stmt.excluded.symbol,
            "side": stmt.excluded.side,
            "volume": stmt.excluded.volume,
            "open_time": stmt.excluded.open_time,
            "close_time": stmt.excluded.close_time,
            "open_price": stmt.excluded.open_price,
            "close_price": stmt.excluded.close_price,
            "commission": stmt.excluded.commission,
            "swap": stmt.excluded.swap,
            "fees": stmt.excluded.fees,
            "pnl": stmt.excluded.pnl,
            "status": stmt.excluded.status,
            "record_type": stmt.excluded.record_type,
            "magic": stmt.excluded.magic,
            "comment": stmt.excluded.comment,
            "raw_json": stmt.excluded.raw_json,
        }
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=["account_id", "provider_trade_id"],
                set_=update_cols,
            )
        )

    # MVP: account_state snapshots are accepted but not persisted yet (dedicated snapshot tables in next step).
    _recompute_daily_metrics(db, payload.account_id)
    db.commit()
    return {"status": "accepted", "account_id": payload.account_id, "deals_upserted": len(payload.deals)}
