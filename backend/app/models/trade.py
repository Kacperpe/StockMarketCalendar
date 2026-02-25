from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TradeRecordType, TradeSide, TradeStatus


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        UniqueConstraint("account_id", "provider_trade_id", name="uq_trades_account_provider_trade_id"),
        Index("ix_trades_account_close_time", "account_id", "close_time"),
        Index("ix_trades_account_symbol", "account_id", "symbol"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    account_id: Mapped[int] = mapped_column(ForeignKey("broker_accounts.id", ondelete="CASCADE"), index=True)
    provider_trade_id: Mapped[str] = mapped_column(String(128))
    symbol: Mapped[str] = mapped_column(String(64))
    side: Mapped[TradeSide] = mapped_column(Enum(TradeSide, name="trade_side"))
    volume: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    open_price: Mapped[Decimal] = mapped_column(Numeric(20, 10))
    close_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 10), nullable=True)
    commission: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    swap: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    fees: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    pnl: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    status: Mapped[TradeStatus] = mapped_column(Enum(TradeStatus, name="trade_status"))
    record_type: Mapped[TradeRecordType] = mapped_column(
        Enum(TradeRecordType, name="trade_record_type"), default=TradeRecordType.DEAL
    )
    magic: Mapped[int | None] = mapped_column(nullable=True)
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    account = relationship("BrokerAccount", back_populates="trades")

