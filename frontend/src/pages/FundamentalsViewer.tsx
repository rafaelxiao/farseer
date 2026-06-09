import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { fundamentalsApi } from "@/api/fundamentals"

export default function FundamentalsViewer() {
  const [symbol, setSymbol] = useState<string | undefined>(undefined)
  const [inputValue, setInputValue] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["fundamentals", symbol],
    queryFn: () => fundamentalsApi.get({ symbol: symbol || undefined, limit: 100 }),
  })

  const handleSearch = () => {
    setSymbol(inputValue.toUpperCase() || undefined)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Fundamentals Viewer</h1>

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
                placeholder="AAPL (leave empty for all)"
              />
            </div>
            <Button onClick={handleSearch}>Search</Button>
          </div>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <CardHeader>
          <CardTitle>Fundamentals Data</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : data && data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">P/E</TableHead>
                  <TableHead className="text-right">P/B</TableHead>
                  <TableHead className="text-right">Market Cap</TableHead>
                  <TableHead className="text-right">EPS</TableHead>
                  <TableHead>Sector</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="font-medium">{row.symbol}</TableCell>
                    <TableCell>{row.date}</TableCell>
                    <TableCell className="text-right">{row.pe_ratio?.toFixed(2) ?? "-"}</TableCell>
                    <TableCell className="text-right">{row.pb_ratio?.toFixed(2) ?? "-"}</TableCell>
                    <TableCell className="text-right">
                      {row.market_cap ? (row.market_cap / 1e9).toFixed(2) + "B" : "-"}
                    </TableCell>
                    <TableCell className="text-right">{row.eps?.toFixed(2) ?? "-"}</TableCell>
                    <TableCell>{row.sector ?? "-"}</TableCell>
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
