from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import TradeRecordType, TradeSide, TradeStatus


class TradeOut(BaseModel):
    id: str
    account_id: int
    provider_trade_id: str
    symbol: str
    side: TradeSide
    volume: Decimal
    open_time: datetime
    close_time: datetime | None
    open_price: Decimal
    close_price: Decimal | None
    commission: Decimal
    swap: Decimal
    fees: Decimal
    pnl: Decimal
    status: TradeStatus
    record_type: TradeRecordType
    magic: int | None
    comment: str | None

    model_config = {"from_attributes": True}


class TradeListResponse(BaseModel):
    items: list[TradeOut]
    total: int

