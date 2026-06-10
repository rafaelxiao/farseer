import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ohlcApi } from "@/api/ohlc"
import OHLCChart from "@/components/shared/OHLCChart"

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
const ADJUSTMENTS = [
  { value: "original", label: "Original" },
  { value: "forward", label: "Forward (前复权)" },
  { value: "backward", label: "Backward (后复权)" },
]

export default function OHLCViewer() {
  const [symbol, setSymbol] = useState("600519.SH")
  const [inputValue, setInputValue] = useState("600519.SH")
  const [timeframe, setTimeframe] = useState("1d")
  const [adjust, setAdjust] = useState("backward")

  const { data, isLoading } = useQuery({
    queryKey: ["ohlc", symbol, timeframe, adjust],
    queryFn: () => ohlcApi.get({ symbol, timeframe, limit: 2000, adjust }),
    enabled: !!symbol,
  })

  const handleSearch = () => {
    setSymbol(inputValue.toUpperCase())
  }

  const latest = data?.[data.length - 1]
  const oldest = data?.[0]

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">OHLC Viewer</h1>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
            <div className="flex gap-2 w-full sm:w-auto">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="flex h-9 w-full sm:w-40 rounded-md border border-input bg-background px-3 py-1 text-sm"
                placeholder="600519.SH"
              />
              <Button size="sm" onClick={handleSearch}>Search</Button>
            </div>

            <div className="flex flex-wrap gap-1">
              {TIMEFRAMES.map((tf) => (
                <Button
                  key={tf}
                  variant={timeframe === tf ? "default" : "outline"}
                  size="sm"
                  className="h-8 px-2 text-xs"
                  onClick={() => setTimeframe(tf)}
                >
                  {tf}
                </Button>
              ))}
            </div>

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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
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
              <div className="text-xs text-muted-foreground">Date Range</div>
              <div className="text-sm font-medium">
                {oldest ? new Date(oldest.timestamp).toLocaleDateString() : "-"}
              </div>
              <div className="text-xs text-muted-foreground">
                → {latest ? new Date(latest.timestamp).toLocaleDateString() : "-"}
              </div>
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
              <Badge variant="outline" className="ml-2 text-xs">
                {adjust}
              </Badge>
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
