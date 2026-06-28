import { useState, useMemo, useRef, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ohlcApi } from "@/api/ohlc"
import OHLCChart from "@/components/shared/OHLCChart"
import OHLCDataTable from "@/components/shared/OHLCDataTable"
import SymbolSearch from "@/components/shared/SymbolSearch"
import ChartSettings, { getChartColors, resetChartColors, type ChartColors } from "@/components/shared/ChartSettings"

const MA_COLORS = ["#f59e0b", "#3b82f6"]
const ADJUSTMENTS = [
  { value: "original", label: "Original" },
  { value: "forward", label: "Forward" },
  { value: "backward", label: "Backward" },
]
type ViewMode = "chart" | "table"

export default function OHLCViewer() {
  const [symbol, setSymbol] = useState("600519.SH")
  const [timeframe, setTimeframe] = useState("1d")
  const [dataSource, setDataSource] = useState("tushare")
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

  // Auto-switch data source: 1m → qmt, 1d → tushare
  const handleTimeframeChange = (tf: string) => {
    setTimeframe(tf)
    if (tf === "1m") setDataSource("qmt")
    if (tf === "1d") setDataSource("tushare")
  }

  // Fetch data
  const { data, isLoading: isDataLoading } = useQuery({
    queryKey: ["ohlc", symbol, timeframe, dataSource, adjust, startDate, endDate],
    queryFn: () => ohlcApi.get({
      symbol, timeframe, limit: 5000, adjust,
      start: startDate || undefined,
      end: endDate || undefined,
      data_source: dataSource,
    }),
    staleTime: 0,
    select: (d) => d || [],
  })

  // Update preserved data only when loading is complete with results
  const lastDataRef = useRef<any[]>([])
  useEffect(() => {
    if (data && data.length > 0) lastDataRef.current = data
  }, [data])
  
  // Only use preserved data during loading, not after empty results
  const displayData = isDataLoading ? (lastDataRef.current.length > 0 ? lastDataRef.current : data) : (data && data.length > 0 ? data : [])

  // Chart data
  const chartData = useMemo(() => {
    if (!displayData || displayData.length === 0) return []
    const sorted = [...displayData].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    return sorted.map(d => ({
      timestamp: d.timestamp,
      open: d.open, high: d.high, low: d.low, close: d.close, volume: d.volume,
    }))
  }, [data])

  // Latest bar
  const currentBar = useMemo(() => chartData[chartData.length - 1], [chartData])

  // MA
  const maPeriods = useMemo(() => {
    const p: number[] = []
    if (ma1 > 0) p.push(ma1)
    if (ma2 > 0) p.push(ma2)
    return p
  }, [ma1, ma2])

  // Persist MA
  const saveMa = (m1: number, m2: number) => {
    localStorage.setItem("farseer-ma-periods", JSON.stringify([m1, m2]))
  }
  const handleMa1Commit = () => {
    const v = Math.max(0, parseInt(maInput1) || 0)
    setMa1(v); setMaInput1(String(v)); saveMa(v, ma2)
  }
  const handleMa2Commit = () => {
    const v = Math.max(0, parseInt(maInput2) || 0)
    setMa2(v); setMaInput2(String(v)); saveMa(ma1, v)
  }

  const handleColorChange = (newColors: ChartColors) => {
    setColors(newColors)
    localStorage.setItem("farseer-chart-colors", JSON.stringify(newColors))
  }
  const handleColorReset = () => {
    const c = resetChartColors()
    setColors(c)
    localStorage.setItem("farseer-chart-colors", JSON.stringify(c))
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <Card>
        <CardContent className="py-3 space-y-3">
          <div className="flex flex-wrap items-end gap-3">
            <SymbolSearch value={symbol} onSelect={setSymbol} />
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Adj</label>
              <div className="flex gap-1">
                {ADJUSTMENTS.map(a => (
                  <button key={a.value} onClick={() => setAdjust(a.value)}
                    className={`px-2.5 py-1 rounded text-xs ${adjust === a.value ? "bg-primary text-primary-foreground" : "border hover:bg-accent"}`}>{a.label}</button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Timeframe</label>
              <div className="flex gap-1">
                {["1d", "1m"].map(tf => (
                  <button key={tf} onClick={() => handleTimeframeChange(tf)}
                    className={`px-2.5 py-1 rounded text-xs ${timeframe === tf ? "bg-primary text-primary-foreground" : "border hover:bg-accent"}`}>{tf}</button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Start</label>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                className="h-8 w-36 rounded border border-input bg-background px-2 text-xs" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">End</label>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                className="h-8 w-36 rounded border border-input bg-background px-2 text-xs" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">View</label>
              <div className="flex gap-1">
                <Button size="sm" variant={viewMode === "chart" ? "default" : "outline"} onClick={() => setViewMode("chart")}>Chart</Button>
                <Button size="sm" variant={viewMode === "table" ? "default" : "outline"} onClick={() => setViewMode("table")}>Table</Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      {currentBar && (
        <div className="grid grid-cols-3 gap-3">
          <Card><CardContent className="py-3"><div className="text-xs text-muted-foreground">Latest Close</div><div className="text-xl font-bold">{currentBar.close.toFixed(2)}</div><div className="text-xs text-muted-foreground">{new Date(currentBar.timestamp).toLocaleDateString()}</div></CardContent></Card>
          <Card><CardContent className="py-3"><div className="text-xs text-muted-foreground">Records</div><div className="text-xl font-bold">{data?.length.toLocaleString()}</div></CardContent></Card>
          <Card><CardContent className="py-3"><div className="text-xs text-muted-foreground">Backward Factor</div><div className="text-xl font-bold">{(data?.[0] as any)?.backward_factor?.toFixed(4) ?? "-"}</div></CardContent></Card>
        </div>
      )}

      {/* Chart / Table */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {symbol} - {timeframe}
              <Badge variant="outline" className="ml-2 text-xs">{adjust}</Badge>
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
              <span className="text-xs text-muted-foreground">{chartData.length} bars</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isDataLoading ? (
            <div className="flex items-center justify-center h-[400px] text-muted-foreground">Loading...</div>
          ) : viewMode === "chart" ? (
            <OHLCChart data={chartData} height={450} colors={colors} logScale={logScale} maPeriods={maPeriods} />
          ) : (
            <OHLCDataTable data={chartData} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
