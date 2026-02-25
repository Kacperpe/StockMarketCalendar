from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.broker_account import BrokerAccount
from app.models.daily_metric import DailyAccountMetric
from app.models.enums import TradeRecordType, TradeStatus
from app.models.trade import Trade
from app.models.user import User
from app.schemas.metrics import (
    DailyMetricListResponse,
    EquityCurvePoint,
    EquityCurveResponse,
    StatsResponse,
)
from app.schemas.trades import TradeListResponse
from app.services.stats import compute_stats_from_closed_trades


router = APIRouter(prefix="/accounts", tags=["data"])


def _get_account_or_404(db: Session, user_id: int, account_id: int) -> BrokerAccount:
    account = db.scalar(select(BrokerAccount).where(BrokerAccount.id == account_id, BrokerAccount.user_id == user_id))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


def _parse_range_token(range_token: str) -> datetime | None:
    now = datetime.now(UTC)
    mapping = {"7d": 7, "30d": 30, "90d": 90}
    if range_token == "all":
        return None
    days = mapping.get(range_token)
    if days is None:
        raise HTTPException(status_code=400, detail="Invalid range")
    return now - timedelta(days=days)


@router.get("/{account_id}/trades", response_model=TradeListResponse)
def get_trades(
    account_id: int,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    symbol: str | None = Query(default=None),
    pnl_sign: str | None = Query(default=None, alias="pnlSign"),
    type_: TradeRecordType | None = Query(default=None, alias="type"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TradeListResponse:
    _get_account_or_404(db, current_user.id, account_id)

    conditions = [Trade.account_id == account_id]
    if from_:
        conditions.append(Trade.close_time >= from_)
    if to:
        conditions.append(Trade.close_time <= to)
    if symbol:
        conditions.append(func.lower(Trade.symbol) == symbol.lower())
    if type_:
        conditions.append(Trade.record_type == type_)
    if pnl_sign == "positive":
        conditions.append(Trade.pnl > 0)
    elif pnl_sign == "negative":
        conditions.append(Trade.pnl < 0)

    stmt = select(Trade).where(and_(*conditions)).order_by(Trade.close_time.desc().nullslast(), Trade.open_time.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = list(db.scalars(stmt.offset(offset).limit(limit)))
    return TradeListResponse(items=items, total=int(total))


@router.get("/{account_id}/daily-metrics", response_model=DailyMetricListResponse)
def get_daily_metrics(
    account_id: int,
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyMetricListResponse:
    _get_account_or_404(db, current_user.id, account_id)
    stmt = select(DailyAccountMetric).where(DailyAccountMetric.account_id == account_id)
    if from_:
        stmt = stmt.where(DailyAccountMetric.date >= from_)
    if to:
        stmt = stmt.where(DailyAccountMetric.date <= to)
    stmt = stmt.order_by(DailyAccountMetric.date.desc())
    return DailyMetricListResponse(items=list(db.scalars(stmt)))


@router.get("/{account_id}/equity-curve", response_model=EquityCurveResponse)
def get_equity_curve(
    account_id: int,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    granularity: str = Query(default="day", pattern="^(day|hour)$"),
    start_balance: Decimal = Query(default=Decimal("0")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EquityCurveResponse:
    _get_account_or_404(db, current_user.id, account_id)

    stmt = select(Trade).where(Trade.account_id == account_id, Trade.status == TradeStatus.CLOSED)
    if from_:
        stmt = stmt.where(Trade.close_time >= from_)
    if to:
        stmt = stmt.where(Trade.close_time <= to)
    trades = list(db.scalars(stmt.order_by(Trade.close_time.asc())))

    tz = ZoneInfo(settings.app_timezone)
    buckets: dict[datetime, Decimal] = {}
    cumulative = Decimal(start_balance)
    points: list[EquityCurvePoint] = []
    method = "balance_from_closed_trades"

    for trade in trades:
        if not trade.close_time:
            continue
        net = Decimal(trade.pnl or 0) - Decimal(trade.commission or 0) - Decimal(trade.swap or 0) - Decimal(trade.fees or 0)
        cumulative += net
        local_dt = trade.close_time.astimezone(tz)
        bucket = local_dt.replace(minute=0, second=0, microsecond=0) if granularity == "hour" else local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        buckets[bucket.astimezone(UTC)] = cumulative

    for ts in sorted(buckets.keys()):
        points.append(EquityCurvePoint(ts=ts, balance=buckets[ts]))
    return EquityCurveResponse(points=points, method=method)


@router.get("/{account_id}/stats", response_model=StatsResponse)
def get_stats(
    account_id: int,
    range_: str = Query(default="30d", alias="range"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatsResponse:
    _get_account_or_404(db, current_user.id, account_id)
    cutoff = _parse_range_token(range_)

    stmt = select(Trade).where(Trade.account_id == account_id, Trade.status == TradeStatus.CLOSED)
    if cutoff:
        stmt = stmt.where(Trade.close_time >= cutoff)
    trades = list(db.scalars(stmt.order_by(Trade.close_time.asc())))
    return StatsResponse(**compute_stats_from_closed_trades(trades))

