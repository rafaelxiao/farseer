import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ohlcApi } from "@/api/ohlc"

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]

export default function OHLCViewer() {
  const [symbol, setSymbol] = useState("AAPL")
  const [timeframe, setTimeframe] = useState("1d")
  const [inputValue, setInputValue] = useState("AAPL")

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["ohlc", symbol, timeframe],
    queryFn: () => ohlcApi.get({ symbol, timeframe, limit: 100 }),
    enabled: !!symbol,
  })

  const handleSearch = () => {
    setSymbol(inputValue.toUpperCase())
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">OHLC Viewer</h1>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium">Symbol</label>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="AAPL"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Timeframe</label>
              <div className="flex gap-1">
                {TIMEFRAMES.map((tf) => (
                  <Button
                    key={tf}
                    variant={timeframe === tf ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTimeframe(tf)}
                  >
                    {tf}
                  </Button>
                ))}
              </div>
            </div>

            <Button onClick={handleSearch}>Search</Button>
          </div>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <CardHeader>
          <CardTitle>{symbol} - {timeframe}</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : data && data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead className="text-right">Open</TableHead>
                  <TableHead className="text-right">High</TableHead>
                  <TableHead className="text-right">Low</TableHead>
                  <TableHead className="text-right">Close</TableHead>
                  <TableHead className="text-right">Volume</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{new Date(row.timestamp).toLocaleString()}</TableCell>
                    <TableCell className="text-right">{row.open.toFixed(2)}</TableCell>
                    <TableCell className="text-right">{row.high.toFixed(2)}</TableCell>
                    <TableCell className="text-right">{row.low.toFixed(2)}</TableCell>
                    <TableCell className="text-right">{row.close.toFixed(2)}</TableCell>
                    <TableCell className="text-right">{row.volume.toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-muted-foreground">No data found</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
