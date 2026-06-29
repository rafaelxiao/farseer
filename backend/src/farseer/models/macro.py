"""
Macro-economic data model.

Stores time-series macro indicators like CPI, PMI, GDP, interest rates, etc.
Design: flat key-value style like Fundamentals, but simpler — no category column.
Each row = one observation for one indicator on one date.
"""

from datetime import date

from sqlalchemy import BigInteger, Date, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from farseer.database import Base
from farseer.models.base import TimestampMixin


class Macro(TimestampMixin, Base):
    __tablename__ = "macro"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Indicator symbol, e.g. "CPI.CN", "PMI.CN", "GDP.US", "FEDFUNDS.US"
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Data source discriminator
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="akshare", index=True)

    # Observation date (monthly or quarterly)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Observation value (always a single float)
    value: Mapped[float] = mapped_column(nullable=False)

    # Flexible extra data (e.g. {"yoy": 0.5, "mom": -0.1} for CPI, {"gdp": ..., "gdp_yoy": ...})
    data: Mapped[str | None] = mapped_column(Text, nullable=True, default="{}")

    __table_args__ = (
        UniqueConstraint("symbol", "data_source", "date", name="uq_macro_sym_src_date"),
        Index("ix_macro_sym_date", "symbol", "date"),
    )
