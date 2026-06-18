"""Trading game API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from farseer.database import async_session_factory
from farseer.models.user import User
from farseer.models.trading_game import TradingGame, GameTrade, GameStats
from farseer.api.v1.auth import get_current_user_dep
from farseer.services.ohlc import OHLCService

router = APIRouter()


async def get_db():
    async with async_session_factory() as db:
        yield db


# Schemas
class StartGameRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    lot_size: int = 100


class TradeAction(BaseModel):
    bar_index: int
    action: str  # buy, sell, hold
    price: float
    quantity: int = 0


class GameResponse(BaseModel):
    id: int
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float
    lot_size: int
    status: str
    created_at: str


class TradeResponse(BaseModel):
    id: int
    bar_index: int
    action: str
    price: float
    quantity: int
    cash_before: float
    cash_after: float
    position_before: int
    position_after: int
    timestamp: str


class StatsResponse(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    avg_holding_bars: float
    profit_factor: float
    sharpe_ratio: float
    final_capital: float
    peak_capital: float
    trade_details: list


@router.post("/start", response_model=GameResponse)
async def start_game(
    req: StartGameRequest,
    user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """Start a new trading game."""
    game = TradingGame(
        user_id=user.id,
        symbol=req.symbol,
        timeframe=req.timeframe,
        start_date=datetime.fromisoformat(req.start_date),
        end_date=datetime.fromisoformat(req.end_date),
        initial_capital=req.initial_capital,
        lot_size=req.lot_size,
        status="active",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    # Create initial stats
    stats = GameStats(
        game_id=game.id,
        final_capital=req.initial_capital,
        peak_capital=req.initial_capital,
    )
    db.add(stats)
    await db.commit()

    return GameResponse(
        id=game.id,
        symbol=game.symbol,
        timeframe=game.timeframe,
        start_date=game.start_date.isoformat(),
        end_date=game.end_date.isoformat(),
        initial_capital=game.initial_capital,
        lot_size=game.lot_size,
        status=game.status,
        created_at=game.created_at.isoformat(),
    )


@router.post("/{game_id}/trade", response_model=TradeResponse)
async def record_trade(
    game_id: int,
    trade: TradeAction,
    user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """Record a trade action."""
    # Get game
    result = await db.execute(
        select(TradingGame).where(TradingGame.id == game_id, TradingGame.user_id == user.id)
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is not active")

    # Get current state
    trades_result = await db.execute(
        select(GameTrade).where(GameTrade.game_id == game_id).order_by(GameTrade.bar_index.desc())
    )
    last_trade = trades_result.scalars().first()

    cash_before = last_trade.cash_after if last_trade else game.initial_capital
    position_before = last_trade.position_after if last_trade else 0

    cash_after = cash_before
    position_after = position_before
    quantity = 0

    if trade.action == "buy":
        # Calculate max lots can buy
        max_quantity = int(cash_before / (trade.price * game.lot_size)) * game.lot_size
        quantity = min(trade.quantity or game.lot_size, max_quantity)
        cost = quantity * trade.price
        cash_after = cash_before - cost
        position_after = position_before + quantity

    elif trade.action == "sell":
        quantity = min(trade.quantity or game.lot_size, position_before)
        proceeds = quantity * trade.price
        cash_after = cash_before + proceeds
        position_after = position_before - quantity

    # Record trade
    game_trade = GameTrade(
        game_id=game_id,
        bar_index=trade.bar_index,
        action=trade.action,
        price=trade.price,
        quantity=quantity,
        cash_before=cash_before,
        cash_after=cash_after,
        position_before=position_before,
        position_after=position_after,
        timestamp=datetime.utcnow(),  # Will be set from frontend
    )
    db.add(game_trade)
    await db.commit()
    await db.refresh(game_trade)

    return TradeResponse(
        id=game_trade.id,
        bar_index=game_trade.bar_index,
        action=game_trade.action,
        price=game_trade.price,
        quantity=game_trade.quantity,
        cash_before=game_trade.cash_before,
        cash_after=game_trade.cash_after,
        position_before=game_trade.position_before,
        position_after=game_trade.position_after,
        timestamp=game_trade.timestamp.isoformat(),
    )


@router.get("/{game_id}/trades", response_model=list[TradeResponse])
async def get_trades(
    game_id: int,
    user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """Get all trades for a game."""
    result = await db.execute(
        select(TradingGame).where(TradingGame.id == game_id, TradingGame.user_id == user.id)
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    trades_result = await db.execute(
        select(GameTrade).where(GameTrade.game_id == game_id).order_by(GameTrade.bar_index)
    )
    trades = trades_result.scalars().all()

    return [
        TradeResponse(
            id=t.id,
            bar_index=t.bar_index,
            action=t.action,
            price=t.price,
            quantity=t.quantity,
            cash_before=t.cash_before,
            cash_after=t.cash_after,
            position_before=t.position_before,
            position_after=t.position_after,
            timestamp=t.timestamp.isoformat(),
        )
        for t in trades
    ]


@router.get("/{game_id}/stats", response_model=StatsResponse)
async def get_stats(
    game_id: int,
    user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """Get game statistics."""
    result = await db.execute(
        select(TradingGame).where(TradingGame.id == game_id, TradingGame.user_id == user.id)
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get trades
    trades_result = await db.execute(
        select(GameTrade).where(GameTrade.game_id == game_id).order_by(GameTrade.bar_index)
    )
    trades = trades_result.scalars().all()

    # Calculate stats
    stats = calculate_stats(trades, game.initial_capital)

    # Update stats in DB
    stats_result = await db.execute(select(GameStats).where(GameStats.game_id == game_id))
    db_stats = stats_result.scalar_one_or_none()
    if db_stats:
        for key, value in stats.items():
            setattr(db_stats, key, value)
        await db.commit()

    return StatsResponse(**stats)


@router.post("/{game_id}/complete")
async def complete_game(
    game_id: int,
    user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """Complete a game and calculate final stats."""
    result = await db.execute(
        select(TradingGame).where(TradingGame.id == game_id, TradingGame.user_id == user.id)
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    game.status = "completed"
    await db.commit()
    return {"message": "Game completed"}


@router.get("/my-games", response_model=list[GameResponse])
async def my_games(
    user: User = Depends(get_current_user_dep),
    db: AsyncSession = Depends(get_db),
):
    """Get all games for current user."""
    result = await db.execute(
        select(TradingGame).where(TradingGame.user_id == user.id).order_by(TradingGame.created_at.desc())
    )
    games = result.scalars().all()

    return [
        GameResponse(
            id=g.id,
            symbol=g.symbol,
            timeframe=g.timeframe,
            start_date=g.start_date.isoformat(),
            end_date=g.end_date.isoformat(),
            initial_capital=g.initial_capital,
            lot_size=g.lot_size,
            status=g.status,
            created_at=g.created_at.isoformat(),
        )
        for g in games
    ]


def calculate_stats(trades: list, initial_capital: float) -> dict:
    """Calculate trading statistics."""
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_return": 0.0,
            "total_return_pct": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "avg_holding_bars": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "final_capital": initial_capital,
            "peak_capital": initial_capital,
            "trade_details": [],
        }

    # Track equity curve
    equity_curve = []
    current_cash = initial_capital
    current_position = 0
    peak_capital = initial_capital
    max_drawdown = 0.0

    # Track completed trades (round trips)
    open_trades = []  # List of (entry_bar, entry_price, quantity)
    completed_trades = []
    total_bars_held = 0

    for trade in trades:
        if trade.action == "buy" and trade.quantity > 0:
            open_trades.append({
                "entry_bar": trade.bar_index,
                "entry_price": trade.price,
                "quantity": trade.quantity,
            })
            current_cash = trade.cash_after
            current_position = trade.position_after

        elif trade.action == "sell" and trade.quantity > 0:
            # Match with open trades (FIFO)
            remaining_to_sell = trade.quantity
            while remaining_to_sell > 0 and open_trades:
                open_trade = open_trades[0]
                if open_trade["quantity"] <= remaining_to_sell:
                    # Full close
                    pnl = (trade.price - open_trade["entry_price"]) * open_trade["quantity"]
                    bars_held = trade.bar_index - open_trade["entry_bar"]
                    completed_trades.append({
                        "entry_bar": open_trade["entry_bar"],
                        "exit_bar": trade.bar_index,
                        "entry_price": open_trade["entry_price"],
                        "exit_price": trade.price,
                        "quantity": open_trade["quantity"],
                        "pnl": pnl,
                        "bars_held": bars_held,
                    })
                    total_bars_held += bars_held
                    remaining_to_sell -= open_trade["quantity"]
                    open_trades.pop(0)
                else:
                    # Partial close
                    pnl = (trade.price - open_trade["entry_price"]) * remaining_to_sell
                    bars_held = trade.bar_index - open_trades[0]["entry_bar"]
                    completed_trades.append({
                        "entry_bar": open_trade["entry_bar"],
                        "exit_bar": trade.bar_index,
                        "entry_price": open_trade["entry_price"],
                        "exit_price": trade.price,
                        "quantity": remaining_to_sell,
                        "pnl": pnl,
                        "bars_held": bars_held,
                    })
                    total_bars_held += bars_held
                    open_trade["quantity"] -= remaining_to_sell
                    remaining_to_sell = 0

            current_cash = trade.cash_after
            current_position = trade.position_after

        # Update equity
        total_equity = current_cash + current_position * trade.price
        equity_curve.append(total_equity)

        # Update peak and drawdown
        if total_equity > peak_capital:
            peak_capital = total_equity
        drawdown = peak_capital - total_equity
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Calculate final stats
    final_trade = trades[-1]
    final_capital = final_trade.cash_after + final_trade.position_after * final_trade.price

    # Win/loss stats
    winning_trades = [t for t in completed_trades if t["pnl"] > 0]
    losing_trades = [t for t in completed_trades if t["pnl"] <= 0]

    total_wins = sum(t["pnl"] for t in winning_trades) if winning_trades else 0
    total_losses = abs(sum(t["pnl"] for t in losing_trades)) if losing_trades else 0

    win_rate = len(winning_trades) / len(completed_trades) * 100 if completed_trades else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else float("inf") if total_wins > 0 else 0
    avg_holding = total_bars_held / len(completed_trades) if completed_trades else 0

    total_return = final_capital - initial_capital
    total_return_pct = (total_return / initial_capital) * 100
    max_drawdown_pct = (max_drawdown / peak_capital) * 100 if peak_capital > 0 else 0

    # Simple Sharpe ratio (annualized, assuming 252 trading days)
    if len(equity_curve) > 1:
        returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] for i in range(1, len(equity_curve))]
        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe_ratio = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0
    else:
        sharpe_ratio = 0

    return {
        "total_trades": len(completed_trades),
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": round(win_rate, 2),
        "total_return": round(total_return, 2),
        "total_return_pct": round(total_return_pct, 2),
        "max_drawdown": round(max_drawdown, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "avg_holding_bars": round(avg_holding, 1),
        "profit_factor": round(profit_factor, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "final_capital": round(final_capital, 2),
        "peak_capital": round(peak_capital, 2),
        "trade_details": [
            {
                "entry_bar": t["entry_bar"],
                "exit_bar": t["exit_bar"],
                "entry_price": t["entry_price"],
                "exit_price": t["exit_price"],
                "quantity": t["quantity"],
                "pnl": round(t["pnl"], 2),
                "bars_held": t["bars_held"],
            }
            for t in completed_trades
        ],
    }
