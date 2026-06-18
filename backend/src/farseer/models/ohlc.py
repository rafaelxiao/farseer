from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from farseer.database import Base
from farseer.models.base import TimestampMixin


class OHLC(TimestampMixin, Base):
    __tablename__ = "ohlc"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="tushare", index=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # 1m, 5m, 1h, 1d, etc.
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Core OHLC
    open: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # Backward adjustment factor (后复权)
    # Stores cumulative adjustment from IPO to this date
    # - backward_adjusted = actual_price * backward_factor
    # - forward_adjusted = actual_price * (backward_factor / latest_backward_factor)
    backward_factor: Mapped[float] = mapped_column(Numeric(18, 10), nullable=False, default=1.0)

    # Flexible extra data (VWAP, turnover, bid/ask, etc.)
    data: Mapped[str | None] = mapped_column(Text, nullable=True, default="{}")  # JSON

    __table_args__ = (
        UniqueConstraint("symbol", "data_source", "timeframe", "timestamp", name="uq_ohlc_sym_src_ts"),
    )
