import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TextInput } from "@/components/ui/text-input"
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
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Fundamentals Viewer</h1>

      <Card>
        <CardContent className="py-3">
          <div className="flex gap-2">
            <TextInput
              size="sm"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Symbol (empty=all)"
              className="w-40"
            />
            <Button size="sm" onClick={handleSearch}>Search</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-base">Fundamentals Data</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : data && data.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs">Symbol</TableHead>
                    <TableHead className="text-xs">Date</TableHead>
                    <TableHead className="text-xs">Category</TableHead>
                    <TableHead className="text-xs">Data</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell className="text-sm font-medium">{row.symbol}</TableCell>
                      <TableCell className="text-sm">{row.date}</TableCell>
                      <TableCell className="text-sm">{row.category ?? "-"}</TableCell>
                      <TableCell className="text-xs max-w-xs truncate">
                        {JSON.stringify(row.data)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No data found</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
