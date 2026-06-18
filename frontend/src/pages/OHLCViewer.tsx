import { useState, useMemo, useEffect, useRef, useCallback } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ohlcApi } from "@/api/ohlc"
import OHLCChart, { type PriceLevel } from "@/components/shared/OHLCChart"
import OHLCDataTable from "@/components/shared/OHLCDataTable"
import SymbolSearch from "@/components/shared/SymbolSearch"
import ChartSettings, { getChartColors, resetChartColors, type ChartColors } from "@/components/shared/ChartSettings"
import PlaybackControls from "@/components/shared/PlaybackControls"
import DatePicker from "@/components/shared/DatePicker"
import { authApi } from "@/api/auth"
import { api } from "@/api/client"

const MA_COLORS = ["#f59e0b", "#3b82f6"]
const ADJUSTMENTS = [
  { value: "original", label: "Original" },
  { value: "forward", label: "Forward" },
  { value: "backward", label: "Backward" },
]
type ViewMode = "chart" | "table"
type AssetType = "stock" | "etf"

const INITIAL_CAPITAL = 10000000  // 10M yuan
const LOT_SIZE = 100

export default function OHLCViewer() {
  const [symbol, setSymbol] = useState("600519.SH")
  const [assetType, setAssetType] = useState<AssetType>("stock")
  const [timeframe, setTimeframe] = useState("1d")
  const [adjust, setAdjust] = useState("backward")
  const [startDate, setStartDate] = useState(() => {
    const d = new Date(); d.setFullYear(d.getFullYear() - 1); return d.toISOString().split("T")[0]
  })
  const [endDate, setEndDate] = useState("")
  const [viewMode, setViewMode] = useState<ViewMode>("chart")
  const [logScale, setLogScale] = useState(false)
  const [ma1, setMa1] = useState<number>(() => {
    try { const s = localStorage.getItem("farseer-ma-periods"); if (s) { const a = JSON.parse(s); return a[0] ?? 20 } } catch {} return 20
  })
  const [ma2, setMa2] = useState<number>(() => {
    try { const s = localStorage.getItem("farseer-ma-periods"); if (s) { const a = JSON.parse(s); return a[1] ?? 50 } } catch {} return 50
  })
  const [maInput1, setMaInput1] = useState(String(ma1))
  const [maInput2, setMaInput2] = useState(String(ma2))
  const [colors, setColors] = useState<ChartColors>(getChartColors)

  // Playback state
  const [playbackMode, setPlaybackMode] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackBar, setPlaybackBar] = useState(0)
  const [speed, setSpeed] = useState(1)
  const [showStartDialog, setShowStartDialog] = useState(false)
  const [playbackStartDate, setPlaybackStartDate] = useState("")
  const intervalRef = useRef<number | null>(null)
  const isAuthenticated = authApi.isAuthenticated()

  // Game state
  const [gameId, setGameId] = useState<number | null>(null)
  const [cash, setCash] = useState(INITIAL_CAPITAL)
  const [position, setPosition] = useState(0)
  const [showStats, setShowStats] = useState(false)
  const [gameStats, setGameStats] = useState<any>(null)
  const [priceLevel, setPriceLevel] = useState<PriceLevel | null>(null)
  const [showPriceLevel, setShowPriceLevel] = useState(false)
  const [tpPercent, setTpPercent] = useState(5)
  const [slPercent, setSlPercent] = useState(3)

  const maPeriods = useMemo(() => {
    const p: number[] = []
    if (ma1 > 0) p.push(ma1)
    if (ma2 > 0) p.push(ma2)
    localStorage.setItem("farseer-ma-periods", JSON.stringify(p))
    return p
  }, [ma1, ma2])

  // Single query for all playback data - get data up to and after selected date
  const { data: allPlaybackData, isLoading: playbackLoading } = useQuery({
    queryKey: ["ohlc-playback-all", symbol, timeframe, adjust, playbackStartDate],
    queryFn: async () => {
      // Get 100 bars before the selected date
      const before = await ohlcApi.get({ symbol, timeframe, limit: 100, adjust, end: playbackStartDate })
      // Get ALL bars after the selected date (no limit)
      const after = await ohlcApi.get({ symbol, timeframe, limit: 10000, adjust, start: playbackStartDate })
      // Combine, removing duplicate of playbackStartDate
      const beforeTimestamps = new Set(before.map(d => d.timestamp))
      const afterFiltered = after.filter(d => !beforeTimestamps.has(d.timestamp))
      return [...before, ...afterFiltered]
    },
    enabled: playbackMode && !!playbackStartDate,
  })

  // Normal view query
  const { data, isLoading } = useQuery({
    queryKey: ["ohlc", symbol, timeframe, adjust, startDate, endDate],
    queryFn: () => ohlcApi.get({
      symbol, timeframe, limit: 5000, adjust,
      start: startDate || undefined,
      end: endDate || undefined,
    }),
    enabled: !playbackMode,
  })

  // Find the start index based on selected date
  const startIndex = useMemo(() => {
    if (!allPlaybackData || !playbackStartDate) return 0
    const idx = allPlaybackData.findIndex(d => {
      const barDate = new Date(d.timestamp).toISOString().split("T")[0]
      return barDate >= playbackStartDate
    })
    return idx >= 0 ? idx : allPlaybackData.length - 1
  }, [allPlaybackData, playbackStartDate])

  // Chart data: only show bars up to current playback position
  const chartData = useMemo(() => {
    if (!playbackMode) return data || []
    if (!allPlaybackData) return []
    return allPlaybackData.slice(0, startIndex + playbackBar + 1)
  }, [playbackMode, allPlaybackData, startIndex, playbackBar, data])

  const displayData = playbackMode ? allPlaybackData : data
  const isDataLoading = playbackMode ? playbackLoading : isLoading

  // Auto-play timer
  useEffect(() => {
    if (isPlaying && playbackMode && allPlaybackData) {
      const maxBar = allPlaybackData.length - startIndex - 1
      const interval = 1000 / speed
      intervalRef.current = window.setInterval(() => {
        setPlaybackBar((prev) => {
          if (prev >= maxBar) {
            setIsPlaying(false)
            return prev
          }
          return prev + 1
        })
      }, interval)
    }
    return () => {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null }
    }
  }, [isPlaying, playbackMode, speed, allPlaybackData, startIndex])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (!playbackMode) return
      const maxBar = (allPlaybackData?.length ?? 0) - startIndex - 1
      switch (e.key) {
        case " ": e.preventDefault(); setIsPlaying(p => !p); break
        case "ArrowLeft": e.preventDefault(); setPlaybackBar(p => Math.max(0, p - 1)); break
        case "ArrowRight": e.preventDefault(); setPlaybackBar(p => Math.min(maxBar, p + 1)); break
        case "r": case "R": e.preventDefault(); setPlaybackBar(0); setIsPlaying(false); break
        case "Escape": e.preventDefault(); handleExitPlayback(); break
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [playbackMode, allPlaybackData, startIndex])

  const handleStartPlayback = useCallback(async (startFrom: string) => {
    setPlaybackStartDate(startFrom)
    setPlaybackMode(true)
    setPlaybackBar(0)
    setIsPlaying(false)
    setGameId(null)
    setCash(INITIAL_CAPITAL)
    setPosition(0)
    setGameStats(null)
  }, [])

  const ensureGameStarted = useCallback(async () => {
    if (gameId || !isAuthenticated) return gameId
    try {
      const res: any = await api.post("/game/start", {
        symbol, timeframe,
        start_date: playbackStartDate,
        end_date: new Date().toISOString().split("T")[0],
        initial_capital: INITIAL_CAPITAL,
        lot_size: LOT_SIZE,
      })
      setGameId(res.id)
      return res.id
    } catch (e) { console.error("Failed to start game:", e); return null }
  }, [gameId, isAuthenticated, symbol, timeframe, playbackStartDate])

  const handleExitPlayback = useCallback(() => {
    setPlaybackMode(false)
    setIsPlaying(false)
    setGameId(null)
    setCash(INITIAL_CAPITAL)
    setPosition(0)
    setGameStats(null)
  }, [])

  const handleTrade = useCallback(async (action: "buy" | "sell" | "hold") => {
    if (!chartData || chartData.length === 0) return
    const currentBar = chartData[chartData.length - 1]
    if (!currentBar) return
    const price = currentBar.close

    // Ensure game is started on first trade
    const activeGameId = await ensureGameStarted()

    if (action === "buy") {
      const maxLots = Math.floor(cash / (price * LOT_SIZE))
      if (maxLots > 0) {
        const qty = maxLots * LOT_SIZE
        setCash(prev => prev - qty * price)
        setPosition(prev => prev + qty)
        if (activeGameId) {
          try {
            await api.post(`/game/${activeGameId}/trade`, { bar_index: playbackBar, action: "buy", price, quantity: qty })
          } catch (e) { console.error(e) }
        }
      }
    } else if (action === "sell") {
      if (position >= LOT_SIZE) {
        const maxLots = Math.floor(position / LOT_SIZE)
        const qty = maxLots * LOT_SIZE
        setCash(prev => prev + qty * price)
        setPosition(prev => prev - qty)
        if (activeGameId) {
          try {
            await api.post(`/game/${activeGameId}/trade`, { bar_index: playbackBar, action: "sell", price, quantity: qty })
          } catch (e) { console.error(e) }
        }
      }
    }

    // Advance to next bar
    const maxBar = (allPlaybackData?.length ?? 0) - startIndex - 1
    setPlaybackBar(prev => Math.min(maxBar, prev + 1))
  }, [chartData, cash, position, playbackBar, allPlaybackData, startIndex, ensureGameStarted])

  const handleLoadStats = useCallback(async () => {
    if (!gameId) return
    try {
      const stats = await api.get(`/game/${gameId}/stats`)
      setGameStats(stats)
      setShowStats(!showStats)
    } catch (e) { console.error(e) }
  }, [gameId, showStats])

  const handleSaveGame = useCallback(async () => {
    if (!gameId) return
    try {
      // Get final stats
      const stats = await api.get(`/game/${gameId}/stats`)
      setGameStats(stats)
      // Complete the game
      await api.post(`/game/${gameId}/complete`, {})
      alert("Game saved! View at Performance page.")
    } catch (e) { console.error(e) }
  }, [gameId])

  const handleMa1Commit = () => { const v = parseInt(maInput1); setMa1(isNaN(v) || v <= 0 ? 0 : v) }
  const handleMa2Commit = () => { const v = parseInt(maInput2); setMa2(isNaN(v) || v <= 0 ? 0 : v) }
  const handleColorChange = (c: ChartColors) => { setColors(c); localStorage.setItem("farseer-chart-colors", JSON.stringify(c)) }
  const handleColorReset = () => { const d = resetChartColors(); setColors(d) }

  // Current bar info
  const currentBar = chartData.length > 0 ? chartData[chartData.length - 1] : null
  const currentPrice = currentBar?.close ?? 0
  const equity = cash + position * currentPrice
  const pnl = equity - INITIAL_CAPITAL
  const maxBuyLots = currentPrice > 0 ? Math.floor(cash / (currentPrice * LOT_SIZE)) : 0
  const canBuy = maxBuyLots > 0
  const canSell = position >= LOT_SIZE

  const maxPlaybackBar = allPlaybackData ? allPlaybackData.length - startIndex - 1 : 0

  const handleSetPriceLevel = useCallback(() => {
    if (currentPrice > 0) {
      setPriceLevel({ price: currentPrice, tpPercent, slPercent })
      setShowPriceLevel(true)
    }
  }, [currentPrice, tpPercent, slPercent])

  const handleClearPriceLevel = useCallback(() => {
    setPriceLevel(null)
    setShowPriceLevel(false)
  }, [])

  return (
    <div className="w-full max-w-6xl mx-auto space-y-4">
      {/* Top Bar */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex border rounded-lg overflow-hidden">
              <button className={`px-4 py-2 text-sm font-medium transition-colors ${assetType === "stock" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:bg-accent"}`} onClick={() => { setAssetType("stock"); setSymbol("") }}>Stocks</button>
              <button className={`px-4 py-2 text-sm font-medium transition-colors ${assetType === "etf" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:bg-accent"}`} onClick={() => { setAssetType("etf"); setSymbol("") }}>ETFs</button>
            </div>
            <div className="flex-1 min-w-[200px]">
              <SymbolSearch value={symbol} onSelect={setSymbol} assetType={assetType} />
            </div>
            <div className="h-6 w-px bg-border" />
            <div className="flex border rounded-lg overflow-hidden">
              <button className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === "chart" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:bg-accent"}`} onClick={() => setViewMode("chart")}>Chart</button>
              <button className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === "table" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:bg-accent"}`} onClick={() => setViewMode("table")}>Table</button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters + Playback */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center gap-2">
            <select value={timeframe} onChange={e => setTimeframe(e.target.value)} className="h-8 rounded border border-input bg-background px-2 text-sm">
              <option value="1d">1d</option>
            </select>
            <div className="h-6 w-px bg-border mx-1" />
            <DatePicker value={startDate} onChange={setStartDate} label="From" />
            <DatePicker value={endDate} onChange={setEndDate} label="To" />
            <div className="h-6 w-px bg-border mx-1" />
            {ADJUSTMENTS.map(adj => (
              <Button key={adj.value} variant={adjust === adj.value ? "default" : "outline"} size="sm" className="h-8" onClick={() => setAdjust(adj.value)}>{adj.label}</Button>
            ))}
            <div className="flex-1" />
            <Button variant={playbackMode ? "default" : "outline"} size="sm" className="h-8 gap-1.5" onClick={() => playbackMode ? handleExitPlayback() : setShowStartDialog(true)}>
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3" /></svg>
              {playbackMode ? "Exit Playback" : "Playback"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Playback Controls */}
      {playbackMode && allPlaybackData && allPlaybackData.length > 0 && (
        <Card>
          <CardContent className="py-3">
            <PlaybackControls
              totalBars={maxPlaybackBar + 1}
              currentBar={playbackBar}
              onBarChange={setPlaybackBar}
              isPlaying={isPlaying}
              onPlayPause={() => setIsPlaying(!isPlaying)}
              speed={speed}
              onSpeedChange={setSpeed}
              onReset={() => { setPlaybackBar(0); setIsPlaying(false) }}
              startDate={allPlaybackData[startIndex] ? new Date(allPlaybackData[startIndex].timestamp).toLocaleDateString() : ""}
              endDate={allPlaybackData[allPlaybackData.length - 1] ? new Date(allPlaybackData[allPlaybackData.length - 1].timestamp).toLocaleDateString() : ""}
              currentDate={currentBar ? new Date(currentBar.timestamp).toLocaleDateString() : ""}
            />
          </CardContent>
        </Card>
      )}

      {/* Summary (non-playback) */}
      {!playbackMode && currentBar && (
        <div className="grid grid-cols-3 gap-3">
          <Card><CardContent className="py-3"><div className="text-xs text-muted-foreground">Latest Close</div><div className="text-xl font-bold">{currentBar.close.toFixed(2)}</div><div className="text-xs text-muted-foreground">{new Date(currentBar.timestamp).toLocaleDateString()}</div></CardContent></Card>
          <Card><CardContent className="py-3"><div className="text-xs text-muted-foreground">Records</div><div className="text-xl font-bold">{data?.length.toLocaleString()}</div></CardContent></Card>
          <Card><CardContent className="py-3"><div className="text-xs text-muted-foreground">Backward Factor</div><div className="text-xl font-bold">{currentBar.backward_factor.toFixed(4)}</div></CardContent></Card>
        </div>
      )}

      {/* Chart + Game */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {symbol} - {timeframe}
              <Badge variant="outline" className="ml-2 text-xs">{adjust}</Badge>
              {playbackMode && <Badge variant="default" className="ml-2 text-xs">Bar {playbackBar + 1}/{maxPlaybackBar + 1}</Badge>}
            </CardTitle>
            <div className="flex items-center gap-3">
              <ChartSettings colors={colors} onChange={handleColorChange} onReset={handleColorReset} />
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" checked={logScale} onChange={e => setLogScale(e.target.checked)} className="h-3.5 w-3.5 rounded border-input" />
                <span className="text-xs text-muted-foreground">Log</span>
              </label>
              <div className="flex items-center gap-1">
                <span className="text-xs font-medium" style={{ color: MA_COLORS[0] }}>MA</span>
                <input type="number" value={maInput1} onChange={e => setMaInput1(e.target.value)} onBlur={handleMa1Commit} onKeyDown={e => e.key === "Enter" && handleMa1Commit()} className="h-6 w-10 rounded border border-input bg-background px-1 text-xs text-center" min="0" />
              </div>
              <div className="flex items-center gap-1">
                <span className="text-xs font-medium" style={{ color: MA_COLORS[1] }}>MA</span>
                <input type="number" value={maInput2} onChange={e => setMaInput2(e.target.value)} onBlur={handleMa2Commit} onKeyDown={e => e.key === "Enter" && handleMa2Commit()} className="h-6 w-10 rounded border border-input bg-background px-1 text-xs text-center" min="0" />
              </div>
              <div className="h-4 w-px bg-border mx-1" />
              {/* Price Level Tool */}
              <div className="flex items-center gap-1">
                {showPriceLevel ? (
                  <>
                    <span className="text-xs text-muted-foreground">TP%</span>
                    <input type="number" value={tpPercent} onChange={e => setTpPercent(Number(e.target.value))} className="h-6 w-10 rounded border border-input bg-background px-1 text-xs text-center" min="1" max="50" />
                    <span className="text-xs text-muted-foreground">SL%</span>
                    <input type="number" value={slPercent} onChange={e => setSlPercent(Number(e.target.value))} className="h-6 w-10 rounded border border-input bg-background px-1 text-xs text-center" min="1" max="50" />
                    <button onClick={handleSetPriceLevel} className="px-2 py-1 text-xs border rounded hover:bg-accent">Update</button>
                    <button onClick={handleClearPriceLevel} className="px-2 py-1 text-xs border rounded hover:bg-accent text-red-500">Clear</button>
                  </>
                ) : (
                  <button onClick={handleSetPriceLevel} className="px-2 py-1 text-xs border rounded hover:bg-accent" title="Set TP/SL levels">TP/SL</button>
                )}
              </div>
              <span className="text-xs text-muted-foreground">{chartData.length} bars</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isDataLoading ? (
            <div className="flex items-center justify-center h-[400px] text-muted-foreground">Loading...</div>
          ) : viewMode === "chart" ? (
            <OHLCChart data={chartData} height={450} colors={colors} logScale={logScale} maPeriods={maPeriods} priceLevel={priceLevel} onPriceLevelChange={setPriceLevel} />
          ) : (
            <OHLCDataTable data={chartData} />
          )}

          {/* Game Panel */}
          {playbackMode && isAuthenticated && currentBar && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex items-center justify-between gap-4 flex-wrap">
                {/* Account */}
                <div className="flex items-center gap-5">
                  <div><div className="text-xs text-muted-foreground">Cash</div><div className="text-sm font-bold">¥{cash.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div></div>
                  <div><div className="text-xs text-muted-foreground">Position</div><div className="text-sm font-bold">{position} shares</div></div>
                  <div><div className="text-xs text-muted-foreground">Price</div><div className="text-sm font-bold">¥{currentPrice.toFixed(2)}</div></div>
                  <div><div className="text-xs text-muted-foreground">Equity</div><div className="text-sm font-bold">¥{equity.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div></div>
                  <div><div className="text-xs text-muted-foreground">P&L</div><div className={`text-sm font-bold ${pnl >= 0 ? "text-green-600" : "text-red-600"}`}>{pnl >= 0 ? "+" : ""}{pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })} ({((pnl / INITIAL_CAPITAL) * 100).toFixed(1)}%)</div></div>
                </div>

                {/* Buttons */}
                <div className="flex items-center gap-2">
                  <button onClick={() => canBuy && handleTrade("buy")} className={`px-5 py-2.5 rounded font-bold text-sm ${canBuy ? "bg-green-600 hover:bg-green-700 text-white" : "bg-gray-200 text-gray-400 cursor-not-allowed"}`}>
                    BUY {maxBuyLots > 0 ? maxBuyLots * LOT_SIZE : ""}
                  </button>
                  <button onClick={() => handleTrade("hold")} className="px-5 py-2.5 rounded font-bold text-sm border hover:bg-accent">
                    HOLD
                  </button>
                  <button onClick={() => canSell && handleTrade("sell")} className={`px-5 py-2.5 rounded font-bold text-sm ${canSell ? "bg-red-600 hover:bg-red-700 text-white" : "bg-gray-200 text-gray-400 cursor-not-allowed"}`}>
                    SELL {position >= LOT_SIZE ? Math.floor(position / LOT_SIZE) * LOT_SIZE : ""}
                  </button>
                  {gameId && (
                    <>
                      <button onClick={handleLoadStats} className="px-4 py-2.5 rounded text-sm border hover:bg-accent ml-1">Stats</button>
                      <button onClick={handleSaveGame} className="px-4 py-2.5 rounded text-sm bg-primary text-primary-foreground hover:bg-primary/90 ml-1">Save</button>
                    </>
                  )}
                </div>
              </div>

              {showStats && gameStats && (
                <div className="mt-3 pt-3 border-t grid grid-cols-4 gap-4 text-center">
                  <div><div className="text-xs text-muted-foreground">Trades</div><div className="text-lg font-bold">{gameStats.total_trades}</div></div>
                  <div><div className="text-xs text-muted-foreground">Win Rate</div><div className="text-lg font-bold">{gameStats.win_rate?.toFixed(1) ?? 0}%</div></div>
                  <div><div className="text-xs text-muted-foreground">Return</div><div className={`text-lg font-bold ${(gameStats.total_return_pct ?? 0) >= 0 ? "text-green-600" : "text-red-600"}`}>{(gameStats.total_return_pct ?? 0).toFixed(2)}%</div></div>
                  <div><div className="text-xs text-muted-foreground">Max DD</div><div className="text-lg font-bold text-red-600">-{(gameStats.max_drawdown_pct ?? 0).toFixed(2)}%</div></div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Start Dialog */}
      {showStartDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowStartDialog(false)} />
          <div className="relative bg-background border rounded-lg shadow-xl p-6 w-[360px]">
            <h2 className="text-lg font-bold mb-1">Start Playback</h2>
            <p className="text-sm text-muted-foreground mb-4">Select start date for playback</p>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-2">Start Date</label>
                <DatePicker value={playbackStartDate || new Date().toISOString().split("T")[0]} onChange={setPlaybackStartDate} />
              </div>
              <div>
                <label className="text-sm font-medium block mb-2">Quick Select</label>
                <div className="grid grid-cols-2 gap-2">
                  {[{ label: "1 Month Ago", days: 30 }, { label: "3 Months Ago", days: 90 }, { label: "6 Months Ago", days: 180 }, { label: "1 Year Ago", days: 365 }, { label: "2 Years Ago", days: 730 }, { label: "From IPO", days: -1 }].map(preset => (
                    <button key={preset.label} onClick={() => {
                      let date: string
                      if (preset.days === -1) { date = "1990-12-19" }
                      else { const d = new Date(); d.setDate(d.getDate() - preset.days); date = d.toISOString().split("T")[0] }
                      handleStartPlayback(date)
                      setShowStartDialog(false)
                    }} className="px-3 py-2 text-sm border rounded hover:bg-accent transition-colors">{preset.label}</button>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowStartDialog(false)} className="px-4 py-2 text-sm border rounded hover:bg-accent">Cancel</button>
              <button onClick={() => { handleStartPlayback(playbackStartDate || new Date().toISOString().split("T")[0]); setShowStartDialog(false) }} className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90">Start</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
