import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ohlcApi } from "@/api/ohlc"
import OHLCChart from "@/components/shared/OHLCChart"
import OHLCDataTable from "@/components/shared/OHLCDataTable"

const ADJUSTMENTS = [
  { value: "original", label: "Original" },
  { value: "forward", label: "Forward" },
  { value: "backward", label: "Backward" },
]

type ViewMode = "chart" | "table"

export default function OHLCViewer() {
  const [symbol, setSymbol] = useState("600519.SH")
  const [inputValue, setInputValue] = useState("600519.SH")
  const [timeframe, setTimeframe] = useState("1d")
  const [adjust, setAdjust] = useState("backward")
  const [startDate, setStartDate] = useState(() => {
    const d = new Date()
    d.setFullYear(d.getFullYear() - 1)
    return d.toISOString().split("T")[0]
  })
  const [endDate, setEndDate] = useState("")
  const [viewMode, setViewMode] = useState<ViewMode>("chart")

  const { data, isLoading } = useQuery({
    queryKey: ["ohlc", symbol, timeframe, adjust, startDate, endDate],
    queryFn: () =>
      ohlcApi.get({
        symbol,
        timeframe,
        limit: 5000,
        adjust,
        start: startDate || undefined,
        end: endDate || undefined,
      }),
    enabled: !!symbol,
  })

  const handleSearch = () => {
    setSymbol(inputValue.toUpperCase())
  }

  const latest = data?.[data.length - 1]

  return (
    <div className="w-full max-w-6xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">OHLC Viewer</h1>

      {/* Filters */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="h-8 w-28 rounded border border-input bg-background px-2 text-sm"
              placeholder="600519.SH"
            />
            <Button size="sm" className="h-8" onClick={handleSearch}>
              Search
            </Button>

            <div className="h-6 w-px bg-border mx-1" />

            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="h-8 rounded border border-input bg-background px-2 text-sm"
            >
              <option value="1d">1d</option>
              <option value="1w" disabled>
                1w (soon)
              </option>
              <option value="1M" disabled>
                1M (soon)
              </option>
            </select>

            <div className="h-6 w-px bg-border mx-1" />

            <label className="text-xs text-muted-foreground">From</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="h-8 rounded border border-input bg-background px-2 text-sm"
            />
            <label className="text-xs text-muted-foreground">To</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="h-8 rounded border border-input bg-background px-2 text-sm"
            />

            <div className="h-6 w-px bg-border mx-1" />

            {ADJUSTMENTS.map((adj) => (
              <Button
                key={adj.value}
                variant={adjust === adj.value ? "default" : "outline"}
                size="sm"
                className="h-8"
                onClick={() => setAdjust(adj.value)}
              >
                {adj.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      {latest && (
        <div className="grid grid-cols-3 gap-3">
          <Card>
            <CardContent className="py-3">
              <div className="text-xs text-muted-foreground">Latest Close</div>
              <div className="text-xl font-bold">{latest.close.toFixed(2)}</div>
              <div className="text-xs text-muted-foreground">
                {new Date(latest.timestamp).toLocaleDateString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-3">
              <div className="text-xs text-muted-foreground">Records</div>
              <div className="text-xl font-bold">{data?.length.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">{timeframe} bars</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-3">
              <div className="text-xs text-muted-foreground">Backward Factor</div>
              <div className="text-xl font-bold">{latest.backward_factor.toFixed(4)}</div>
              <div className="text-xs text-muted-foreground">from IPO</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Chart / Table */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {symbol} - {timeframe}
              <Badge variant="outline" className="ml-2 text-xs">
                {adjust}
              </Badge>
            </CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {data?.length.toLocaleString()} records
              </span>
              <div className="flex border rounded">
                <button
                  className={`px-2 py-1 text-xs ${
                    viewMode === "chart"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent"
                  }`}
                  onClick={() => setViewMode("chart")}
                >
                  Chart
                </button>
                <button
                  className={`px-2 py-1 text-xs ${
                    viewMode === "table"
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent"
                  }`}
                  onClick={() => setViewMode("table")}
                >
                  Table
                </button>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-[400px] text-muted-foreground">
              Loading...
            </div>
          ) : viewMode === "chart" ? (
            <OHLCChart data={data || []} height={500} />
          ) : (
            <OHLCDataTable data={data || []} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
