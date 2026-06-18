import { useState, useEffect, useMemo } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api } from "@/api/client"

interface TradeAction {
  bar_index: number
  action: "buy" | "sell" | "hold"
  price: number
  quantity: number
}

interface GameState {
  gameId: number | null
  cash: number
  position: number
  trades: TradeAction[]
  currentBar: number
}

interface GameStats {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  total_return: number
  total_return_pct: number
  max_drawdown: number
  max_drawdown_pct: number
  avg_holding_bars: number
  profit_factor: number
  sharpe_ratio: number
  final_capital: number
  peak_capital: number
  trade_details: any[]
}

interface TradingGamePanelProps {
  symbol: string
  timeframe: string
  currentPrice: number
  currentBar: number
  totalBars: number
  startDate: string
  endDate: string
  onTrade: (action: "buy" | "sell" | "hold") => void
  isPlaying: boolean
}

const INITIAL_CAPITAL = 100000
const LOT_SIZE = 100

export default function TradingGamePanel({
  symbol,
  timeframe,
  currentPrice,
  currentBar,
  totalBars,
  startDate,
  endDate,
  onTrade,
  isPlaying,
}: TradingGamePanelProps) {
  const [gameId, setGameId] = useState<number | null>(null)
  const [cash, setCash] = useState(INITIAL_CAPITAL)
  const [position, setPosition] = useState(0)
  const [trades, setTrades] = useState<TradeAction[]>([])
  const [showStats, setShowStats] = useState(false)

  // Start game mutation
  const startGame = useMutation({
    mutationFn: async () => {
      const res = await api.post("/game/start", {
        symbol,
        timeframe,
        start_date: startDate,
        end_date: endDate,
        initial_capital: INITIAL_CAPITAL,
        lot_size: LOT_SIZE,
      })
      return res as any
    },
    onSuccess: (data) => {
      setGameId(data.id)
      setCash(INITIAL_CAPITAL)
      setPosition(0)
      setTrades([])
    },
  })

  // Record trade mutation
  const recordTrade = useMutation({
    mutationFn: async (trade: TradeAction) => {
      if (!gameId) return
      return api.post(`/game/${gameId}/trade`, trade)
    },
  })

  // Get stats
  const { data: stats } = useQuery<GameStats>({
    queryKey: ["game-stats", gameId],
    queryFn: () => api.get(`/game/${gameId}/stats`),
    enabled: !!gameId && showStats,
  })

  // Handle trade action
  const handleAction = (action: "buy" | "sell" | "hold") => {
    if (!gameId) {
      // Start game first
      startGame.mutate()
      return
    }

    const quantity = action === "hold" ? 0 : LOT_SIZE

    const trade: TradeAction = {
      bar_index: currentBar,
      action,
      price: currentPrice,
      quantity,
    }

    // Update local state
    if (action === "buy") {
      const maxLots = Math.floor(cash / (currentPrice * LOT_SIZE))
      const actualQuantity = Math.min(LOT_SIZE, maxLots * LOT_SIZE)
      if (actualQuantity > 0) {
        setCash((prev) => prev - actualQuantity * currentPrice)
        setPosition((prev) => prev + actualQuantity)
      }
    } else if (action === "sell") {
      const sellQuantity = Math.min(LOT_SIZE, position)
      if (sellQuantity > 0) {
        setCash((prev) => prev + sellQuantity * currentPrice)
        setPosition((prev) => prev - sellQuantity)
      }
    }

    setTrades((prev) => [...prev, trade])
    recordTrade.mutate(trade)
    onTrade(action)
  }

  // Calculate current equity
  const equity = useMemo(() => {
    return cash + position * currentPrice
  }, [cash, position, currentPrice])

  const pnl = equity - INITIAL_CAPITAL
  const pnlPct = (pnl / INITIAL_CAPITAL) * 100

  const canBuy = cash >= currentPrice * LOT_SIZE
  const canSell = position > 0

  return (
    <div className="space-y-4">
      {/* Game Header */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              Trading Game
              {gameId && <Badge variant="default">Active</Badge>}
            </CardTitle>
            {!gameId && (
              <Button size="sm" onClick={() => startGame.mutate()} disabled={startGame.isPending}>
                Start Game
              </Button>
            )}
            {gameId && (
              <Button size="sm" variant="outline" onClick={() => setShowStats(!showStats)}>
                {showStats ? "Hide Stats" : "Show Stats"}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!gameId ? (
            <div className="text-center py-4 text-muted-foreground">
              <p>Click "Start Game" to begin trading</p>
              <p className="text-sm mt-1">Initial capital: ¥{INITIAL_CAPITAL.toLocaleString()} | Lot size: {LOT_SIZE}</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-muted-foreground">Cash</div>
                <div className="text-lg font-bold">¥{cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Position</div>
                <div className="text-lg font-bold">{position} shares</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Equity</div>
                <div className="text-lg font-bold">¥{equity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">P&L</div>
                <div className={`text-lg font-bold ${pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {pnl >= 0 ? "+" : ""}{pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  <span className="text-sm ml-1">({pnlPct.toFixed(2)}%)</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Trade Actions */}
      {gameId && (
        <Card>
          <CardContent className="py-3">
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="default"
                size="lg"
                onClick={() => handleAction("buy")}
                disabled={!canBuy || isPlaying}
                className="bg-green-600 hover:bg-green-700 min-w-[100px]"
              >
                BUY
              </Button>
              <Button
                variant="outline"
                size="lg"
                onClick={() => handleAction("hold")}
                disabled={isPlaying}
                className="min-w-[100px]"
              >
                HOLD
              </Button>
              <Button
                variant="destructive"
                size="lg"
                onClick={() => handleAction("sell")}
                disabled={!canSell || isPlaying}
                className="min-w-[100px]"
              >
                SELL
              </Button>
            </div>
            <div className="text-center text-xs text-muted-foreground mt-2">
              Price: ¥{currentPrice.toFixed(2)} | Lot: {LOT_SIZE} shares | Cost: ¥{(currentPrice * LOT_SIZE).toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      {showStats && stats && (
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-base">Game Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-muted-foreground">Total Trades</div>
                <div className="text-lg font-bold">{stats.total_trades}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Win Rate</div>
                <div className="text-lg font-bold">{stats.win_rate.toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Win/Loss</div>
                <div className="text-lg font-bold">
                  <span className="text-green-600">{stats.winning_trades}</span>
                  {" / "}
                  <span className="text-red-600">{stats.losing_trades}</span>
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Profit Factor</div>
                <div className="text-lg font-bold">{stats.profit_factor.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Total Return</div>
                <div className={`text-lg font-bold ${stats.total_return >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {stats.total_return >= 0 ? "+" : ""}{stats.total_return_pct.toFixed(2)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Max Drawdown</div>
                <div className="text-lg font-bold text-red-600">-{stats.max_drawdown_pct.toFixed(2)}%</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Avg Holding</div>
                <div className="text-lg font-bold">{stats.avg_holding_bars.toFixed(1)} bars</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Sharpe Ratio</div>
                <div className="text-lg font-bold">{stats.sharpe_ratio.toFixed(2)}</div>
              </div>
            </div>

            {/* Trade History */}
            {stats.trade_details.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium mb-2">Trade History</h4>
                <div className="max-h-48 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-1">Entry</th>
                        <th className="text-left py-1">Exit</th>
                        <th className="text-right py-1">Entry Price</th>
                        <th className="text-right py-1">Exit Price</th>
                        <th className="text-right py-1">Qty</th>
                        <th className="text-right py-1">P&L</th>
                        <th className="text-right py-1">Bars</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.trade_details.map((t, i) => (
                        <tr key={i} className="border-b">
                          <td className="py-1">Bar {t.entry_bar}</td>
                          <td className="py-1">Bar {t.exit_bar}</td>
                          <td className="py-1 text-right">¥{t.entry_price.toFixed(2)}</td>
                          <td className="py-1 text-right">¥{t.exit_price.toFixed(2)}</td>
                          <td className="py-1 text-right">{t.quantity}</td>
                          <td className={`py-1 text-right ${t.pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                            {t.pnl >= 0 ? "+" : ""}¥{t.pnl.toFixed(2)}
                          </td>
                          <td className="py-1 text-right">{t.bars_held}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
