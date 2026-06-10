import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select } from "@/components/ui/select"
import { DateInput } from "@/components/ui/date-input"
import { TextInput } from "@/components/ui/text-input"
import { ohlcApi } from "@/api/ohlc"
import OHLCChart from "@/components/shared/OHLCChart"

const TIMEFRAME_OPTIONS = [
  { value: "1d", label: "1d" },
  { value: "1w", label: "1w (soon)", disabled: true },
  { value: "1M", label: "1M (soon)", disabled: true },
]

const ADJUST_OPTIONS = [
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
    <div className="w-full max-w-6xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">OHLC Viewer</h1>

      {/* Filters */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-end gap-3">
            <TextInput
              size="sm"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="600519.SH"
              className="w-28"
            />
            <Button size="sm" onClick={handleSearch}>Search</Button>

            <div className="h-6 w-px bg-border" />

            <Select
              size="sm"
              options={TIMEFRAME_OPTIONS}
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
            />

            <div className="h-6 w-px bg-border" />

            <DateInput size="sm" label="From" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            <DateInput size="sm" label="To" value={endDate} onChange={(e) => setEndDate(e.target.value)} />

            <div className="h-6 w-px bg-border" />

            {ADJUST_OPTIONS.map((adj) => (
              <Button
                key={adj.value}
                variant={adjust === adj.value ? "default" : "outline"}
                size="sm"
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

      {/* Chart */}
      <Card>
        <CardHeader className="py-3">
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
