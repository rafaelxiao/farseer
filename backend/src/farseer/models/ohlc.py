from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from farseer.database import Base
from farseer.models.base import TimestampMixin


class OHLC(TimestampMixin, Base):
    __tablename__ = "ohlc"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # 1m, 5m, 1h, 1d, etc.
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Core OHLC
    open: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # Adjustment factor (incorporates splits, dividends, etc.)
    # adjusted_price = price * adjustor_factor
    adjustor_factor: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=1.0)

    # Flexible extra data (VWAP, turnover, bid/ask, etc.)
    data: Mapped[str | None] = mapped_column(Text, nullable=True, default="{}")  # JSON

    __table_args__ = (
        Index("ix_ohlc_symbol_timeframe_timestamp", "symbol", "timeframe", "timestamp", unique=True),
    )
