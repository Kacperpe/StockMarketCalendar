from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class DailyMetricOut(BaseModel):
    account_id: int
    date: date
    realized_pnl: Decimal
    commissions: Decimal
    swaps: Decimal
    fees: Decimal
    net_pnl: Decimal
    end_balance: Decimal | None
    end_equity: Decimal | None

    model_config = {"from_attributes": True}


class DailyMetricListResponse(BaseModel):
    items: list[DailyMetricOut]


class EquityCurvePoint(BaseModel):
    ts: datetime
    balance: Decimal


class EquityCurveResponse(BaseModel):
    points: list[EquityCurvePoint]
    method: str


class StatsResponse(BaseModel):
    win_rate: float
    profit_factor: float | None
    avg_win: Decimal
    avg_loss: Decimal
    expectancy: Decimal
    best_day: Decimal | None
    worst_day: Decimal | None
    max_drawdown: Decimal
    total_trades: int
    wins: int
    losses: int
    streak_wins: int
    streak_losses: int

