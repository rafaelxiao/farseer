from datetime import date

from sqlalchemy import BigInteger, Date, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from farseer.database import Base
from farseer.models.base import TimestampMixin


class Fundamentals(TimestampMixin, Base):
    __tablename__ = "fundamentals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # e.g. "income", "balance_sheet", "custom"

    # All data stored here as JSON string
    data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # JSON: {"pe_ratio": 15.2, "revenue": 1000000, ...}

    __table_args__ = (
        Index("ix_fundamentals_symbol_date_category", "symbol", "date", "category", unique=True),
    )
