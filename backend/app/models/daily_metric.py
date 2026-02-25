from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyAccountMetric(Base):
    __tablename__ = "daily_account_metrics"
    __table_args__ = (Index("ix_daily_account_metrics_account_date", "account_id", "date"),)

    account_id: Mapped[int] = mapped_column(
        ForeignKey("broker_accounts.id", ondelete="CASCADE"), primary_key=True
    )
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    commissions: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    swaps: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    fees: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    net_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    end_balance: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    end_equity: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)

    account = relationship("BrokerAccount", back_populates="daily_metrics")

