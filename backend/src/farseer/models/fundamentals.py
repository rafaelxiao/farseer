from datetime import date

from sqlalchemy import BigInteger, Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from farseer.database import Base
from farseer.models.base import TimestampMixin


class Fundamentals(TimestampMixin, Base):
    __tablename__ = "fundamentals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Common fundamentals (extend as needed)
    pe_ratio: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    pb_ratio: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    revenue: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    net_income: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    eps: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    dividend_yield: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Flexible extra data
    extra: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string for additional fields
