from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AccountStatus, BrokerProvider


class BrokerAccount(Base):
    __tablename__ = "broker_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[BrokerProvider] = mapped_column(Enum(BrokerProvider, name="broker_provider"))
    name: Mapped[str] = mapped_column(String(120))
    currency: Mapped[str] = mapped_column(String(16))
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status"), default=AccountStatus.NEW
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="broker_accounts")
    credentials = relationship(
        "AccountCredential", back_populates="account", uselist=False, cascade="all, delete-orphan"
    )
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")
    daily_metrics = relationship("DailyAccountMetric", back_populates="account", cascade="all, delete-orphan")

