from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class MT5AccountState(BaseModel):
    balance: Decimal | None = None
    equity: Decimal | None = None
    currency: str | None = None
    timestamp: datetime | None = None


class MT5Deal(BaseModel):
    provider_trade_id: str = Field(alias="deal_id")
    symbol: str
    side: str
    volume: Decimal
    open_time: datetime
    close_time: datetime | None = None
    open_price: Decimal
    close_price: Decimal | None = None
    commission: Decimal = Decimal("0")
    swap: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    pnl: Decimal = Decimal("0")
    status: str = "closed"
    magic: int | None = None
    comment: str | None = None
    raw_json: dict[str, Any] | None = None


class MT5Position(BaseModel):
    position_id: str
    symbol: str
    side: str
    volume: Decimal
    open_time: datetime
    open_price: Decimal
    pnl: Decimal | None = None
    raw_json: dict[str, Any] | None = None


class MT5SnapshotRequest(BaseModel):
    account_id: int
    account_state: MT5AccountState | None = None
    deals: list[MT5Deal] = Field(default_factory=list)
    positions: list[MT5Position] = Field(default_factory=list)
    nonce: str | None = None
    timestamp: datetime | None = None
