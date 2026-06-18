"""Trading game models."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from farseer.models.base import Base


class TradingGame(Base):
    __tablename__ = "trading_games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), default="1d")
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, default=100000.0)
    lot_size = Column(Integer, default=100)
    status = Column(String(20), default="active")  # active, completed, abandoned
    created_at = Column(DateTime, default=datetime.utcnow)


class GameTrade(Base):
    __tablename__ = "game_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("trading_games.id"), nullable=False)
    bar_index = Column(Integer, nullable=False)
    action = Column(String(10), nullable=False)  # buy, sell, hold
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    cash_before = Column(Float, nullable=False)
    cash_after = Column(Float, nullable=False)
    position_before = Column(Integer, default=0)
    position_after = Column(Integer, default=0)
    timestamp = Column(DateTime, nullable=False)  # Bar timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


class GameStats(Base):
    __tablename__ = "game_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("trading_games.id"), nullable=False, unique=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    total_return_pct = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    avg_holding_bars = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    final_capital = Column(Float, default=0.0)
    peak_capital = Column(Float, default=0.0)
    trade_details = Column(JSON, default=[])  # List of trade pairs
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
