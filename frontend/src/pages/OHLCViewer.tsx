import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ohlcApi } from "@/api/ohlc"
import OHLCChart from "@/components/shared/OHLCChart"

const ADJUSTMENTS = [
  { value: "original", label: "Original" },
  { value: "forward", label: "Forward" },
  { value: "backward", label: "Backward" },
]

export default function OHLCViewer() {
  const [symbol, setSymbol] = useState("600519.SH")
  const [inputValue, setInputValue] = useState("600519.SH")
  const [timeframe, setTimeframe] = useState("1d")
  const [adjust, setAdjust] = useState("backward")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["ohlc", symbol, timeframe, adjust, startDate, endDate],
    queryFn: () => ohlcApi.get({
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
    <div className="max-w-6xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">OHLC Viewer</h1>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end flex-wrap">
            {/* Symbol */}
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="flex h-9 w-32 rounded-md border border-input bg-background px-3 py-1 text-sm"
                placeholder="600519.SH"
              />
              <Button size="sm" onClick={handleSearch}>Search</Button>
            </div>

            {/* Timeframe dropdown */}
            <div className="flex items-center gap-2">
              <label className="text-xs text-muted-foreground">TF</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              >
                <option value="1d">1d</option>
                <option value="1w" disabled>1w (soon)</option>
                <option value="1M" disabled>1M (soon)</option>
              </select>
            </div>

            {/* Date range */}
            <div className="flex items-center gap-2">
              <label className="text-xs text-muted-foreground">From</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              />
              <label className="text-xs text-muted-foreground">To</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              />
            </div>

            {/* Adjustment */}
            <div className="flex gap-1">
              {ADJUSTMENTS.map((adj) => (
                <Button
                  key={adj.value}
                  variant={adjust === adj.value ? "default" : "outline"}
                  size="sm"
                  className="h-8 px-2 text-xs"
                  onClick={() => setAdjust(adj.value)}
                >
                  {adj.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      {latest && (
        <div className="grid grid-cols-3 gap-3">
          <Card>
            <CardContent className="pt-4 pb-3">
              <div className="text-xs text-muted-foreground">Latest Close</div>
              <div className="text-xl font-bold">{latest.close.toFixed(2)}</div>
              <div className="text-xs text-muted-foreground">
                {new Date(latest.timestamp).toLocaleDateString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-3">
              <div className="text-xs text-muted-foreground">Records</div>
              <div className="text-xl font-bold">{data?.length.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">{timeframe} bars</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-3">
              <div className="text-xs text-muted-foreground">Backward Factor</div>
              <div className="text-xl font-bold">{latest.backward_factor.toFixed(4)}</div>
              <div className="text-xs text-muted-foreground">from IPO</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Chart */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {symbol} - {timeframe}
              <Badge variant="outline" className="ml-2 text-xs">{adjust}</Badge>
            </CardTitle>
            <div className="text-xs text-muted-foreground">
              {data?.length.toLocaleString()} records
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-[400px] text-muted-foreground">
              Loading...
            </div>
          ) : (
            <OHLCChart data={data || []} height={500} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
