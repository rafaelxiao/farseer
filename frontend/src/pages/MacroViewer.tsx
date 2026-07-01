import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { macroApi } from "@/api/macro"
import FundamentalChart from "@/components/shared/FundamentalChart"

// Indicator metadata: label, color for chart, description
const INDICATOR_META: Record<string, { label: string; color: string; desc: string; unit: string }> = {
  "CPI.CN": { label: "CPI (China)", color: "#ef4444", desc: "Consumer Price Index YoY%", unit: "%" },
  "PPI.CN": { label: "PPI (China)", color: "#f59e0b", desc: "Producer Price Index YoY%", unit: "%" },
  "PMI.CN": { label: "PMI (China)", color: "#22c55e", desc: "Manufacturing PMI", unit: "" },
  "GDP.CN": { label: "GDP (China)", color: "#3b82f6", desc: "GDP Growth YoY%", unit: "%" },
  "M2.CN": { label: "M2 Supply", color: "#8b5cf6", desc: "M2 Money Supply YoY%", unit: "%" },
  "LPR1Y.CN": { label: "LPR 1Y", color: "#06b6d4", desc: "Loan Prime Rate 1Y", unit: "%" },
  "LPR5Y.CN": { label: "LPR 5Y", color: "#ec4899", desc: "Loan Prime Rate 5Y", unit: "%" },
  "FX_USDCNY": { label: "USD/CNY", color: "#6366f1", desc: "Exchange Rate (÷100)", unit: "" },
  "FX_RESERVES.CN": { label: "FX Reserves", color: "#14b8a6", desc: "Foreign Exchange Reserves ($100M)", unit: "" },
  "CPI.US": { label: "CPI (US) YoY", color: "#dc2626", desc: "US CPI YoY% — through 2026-05", unit: "%" },
  "CPI_LEVEL.US": { label: "CPI Level (US)", color: "#ef4444", desc: "US CPI absolute level (1970-)", unit: "" },
  "FEDFUNDS.US": { label: "Fed Funds Rate", color: "#1e40af", desc: "US Federal Funds Rate", unit: "%" },
  "UNEMPLOYMENT.US": { label: "Unemployment (US)", color: "#7c3aed", desc: "US Unemployment Rate", unit: "%" },
  "NONFARM.US": { label: "Non-Farm (US)", color: "#059669", desc: "US Non-Farm Payrolls", unit: "K" },
  "CORE_CPI.US": { label: "Core CPI (US)", color: "#b91c1c", desc: "US Core CPI (ex food/energy)", unit: "" },
  "RETAIL.US": { label: "Retail (US)", color: "#0ea5e9", desc: "US Retail Sales MoM%", unit: "%" },
  "ISM_PMI.US": { label: "ISM PMI (US)", color: "#ca8a04", desc: "US ISM Manufacturing PMI", unit: "" },
  "PPI.US": { label: "PPI (US)", color: "#d97706", desc: "US Producer Price Index", unit: "%" },
  "RRR.CN": { label: "RRR (China)", color: "#7c3aed", desc: "PBOC Reserve Requirement Ratio", unit: "%" },
  "TRADE_BALANCE.CN": { label: "Trade Balance", color: "#2563eb", desc: "China Trade Balance ($100M)", unit: "" },
  "INDUSTRIAL_PROD.CN": { label: "Industrial Prod", color: "#9333ea", desc: "China Industrial Production YoY%", unit: "%" },
  "SOCIAL_FIN.CN": { label: "Social Financing", color: "#0891b2", desc: "China Social Financing (100M CNY)", unit: "" },
  "UNEMPLOY.CN": { label: "Unemploy (CN)", color: "#4f46e5", desc: "China Urban Unemployment Rate", unit: "%" },
}

// Group indicators by country
const INDICATOR_GROUPS: { label: string; symbols: string[] }[] = [
  { label: "💰 China Prices", symbols: ["CPI.CN", "PPI.CN"] },
  { label: "🏭 China Activity", symbols: ["PMI.CN", "GDP.CN", "INDUSTRIAL_PROD.CN", "TRADE_BALANCE.CN"] },
  { label: "💵 China Monetary", symbols: ["M2.CN", "LPR1Y.CN", "LPR5Y.CN", "RRR.CN", "SOCIAL_FIN.CN"] },
  { label: "🌐 China FX & Jobs", symbols: ["FX_USDCNY", "FX_RESERVES.CN", "UNEMPLOY.CN"] },
  { label: "🇺🇸 US Macro", symbols: ["CPI.US", "CPI_LEVEL.US", "CORE_CPI.US", "PPI.US", "FEDFUNDS.US", "UNEMPLOYMENT.US", "NONFARM.US", "RETAIL.US", "ISM_PMI.US"] },
]

function formatValue(value: number): string {
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(2)}M`
  if (Math.abs(value) >= 1e4) return `${(value / 1e4).toFixed(2)}万`
  return value.toFixed(2)
}

export default function MacroViewer() {
  const [selectedSymbol, setSelectedSymbol] = useState("CPI.CN")
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart")
  const [startDate, setStartDate] = useState("2010-01-01")
  const [endDate, setEndDate] = useState("")

  // Fetch available symbols
  const { data: symbols } = useQuery({
    queryKey: ["macro-symbols"],
    queryFn: () => macroApi.listSymbols(),
  })

  // Fetch data for selected indicator
  const { data: records } = useQuery({
    queryKey: ["macro-data", selectedSymbol, startDate, endDate],
    queryFn: () => macroApi.query(selectedSymbol, undefined, startDate || undefined, endDate || undefined, 2000),
    enabled: !!selectedSymbol,
    staleTime: 5 * 60 * 1000,
  })

  // Sort records chronologically ascending (for chart)
  const sortedRecords = useMemo(() => {
    if (!records) return []
    return [...records].sort((a, b) => a.date.localeCompare(b.date))
  }, [records])

  // Sort descending (most recent first) for table
  const tableRecords = useMemo(() => {
    return [...sortedRecords].reverse()
  }, [sortedRecords])

  // Transform to FundamentalChart format
  const chartData = useMemo(() => {
    return sortedRecords.map((r) => ({
      date: r.date.replace(/-/g, ""),
      data: { value: r.value },
    }))
  }, [sortedRecords])

  // Latest value for summary card
  const latestRecord = useMemo(() => {
    if (!records || records.length === 0) return null
    return records.reduce((latest, r) => (r.date > latest.date ? r : latest), records[0])
  }, [records])

  // Stats
  const stats = useMemo(() => {
    if (!records || records.length === 0) return null
    const values = records.map((r) => r.value).filter((v) => v !== null) as number[]
    if (values.length === 0) return null
    return {
      count: values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      latest: values[0],
    }
  }, [records])

  // Current indicator metadata
  const meta = INDICATOR_META[selectedSymbol] || { label: selectedSymbol, color: "#3b82f6", desc: "", unit: "" }

  // Check which symbols from the API are in our known list
  const availableSymbols = useMemo(() => {
    if (!symbols) return new Set<string>()
    return new Set(symbols.map((s) => s.symbol))
  }, [symbols])

  return (
    <div className="w-full max-w-6xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Macro Economics</h1>
        <div className="flex border rounded">
          <button
            className={`px-3 py-1.5 text-sm ${
              viewMode === "chart" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
            }`}
            onClick={() => setViewMode("chart")}
          >
            Chart
          </button>
          <button
            className={`px-3 py-1.5 text-sm ${
              viewMode === "table" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
            }`}
            onClick={() => setViewMode("table")}
          >
            Table
          </button>
        </div>
      </div>

      {/* Indicator Selector */}
      <Card>
        <CardContent className="py-3">
          <div className="space-y-3">
            {INDICATOR_GROUPS.map((group) => (
              <div key={group.label} className="space-y-1.5">
                <div className="text-xs text-muted-foreground">{group.label}</div>
                <div className="flex flex-wrap gap-1.5">
                  {group.symbols.map((sym) => {
                    const m = INDICATOR_META[sym] || { label: sym, color: "#666", desc: "" }
                    const isAvailable = availableSymbols.has(sym)
                    if (!isAvailable) return null
                    return (
                      <button
                        key={sym}
                        onClick={() => setSelectedSymbol(sym)}
                        className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                          selectedSymbol === sym
                            ? "text-white border-transparent font-medium"
                            : "text-muted-foreground hover:bg-accent border-muted"
                        }`}
                        style={
                          selectedSymbol === sym ? { backgroundColor: m.color, borderColor: m.color } : undefined
                        }
                        title={m.desc}
                      >
                        {m.label}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      {latestRecord && stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="p-3 rounded-lg border bg-card">
            <div className="text-xs text-muted-foreground mb-1">Latest ({latestRecord.date})</div>
            <div className="text-lg font-semibold">
              {formatValue(latestRecord.value)}
              {meta.unit && <span className="text-sm ml-1 font-normal">{meta.unit}</span>}
            </div>
          </div>
          <div className="p-3 rounded-lg border bg-card">
            <div className="text-xs text-muted-foreground mb-1">Count</div>
            <div className="text-lg font-semibold">{stats.count}</div>
          </div>
          <div className="p-3 rounded-lg border bg-card">
            <div className="text-xs text-muted-foreground mb-1">Min</div>
            <div className="text-lg font-semibold">{formatValue(stats.min)}</div>
          </div>
          <div className="p-3 rounded-lg border bg-card">
            <div className="text-xs text-muted-foreground mb-1">Max</div>
            <div className="text-lg font-semibold">{formatValue(stats.max)}</div>
          </div>
          <div className="p-3 rounded-lg border bg-card">
            <div className="text-xs text-muted-foreground mb-1">Avg</div>
            <div className="text-lg font-semibold">{formatValue(stats.avg)}</div>
          </div>
        </div>
      )}

      {/* Date Filter */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="secondary">{meta.label}</Badge>
            <div className="h-6 w-px bg-border" />
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
            {endDate && (
              <button
                onClick={() => setEndDate("")}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Content: Chart or Table */}
      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-base">{meta.label} — {meta.desc}</CardTitle>
        </CardHeader>
        <CardContent>
          {viewMode === "chart" ? (
            chartData.length > 0 ? (
              <FundamentalChart
                data={chartData}
                metricKey="value"
                label={meta.label}
                height={450}
                color={meta.color}
              />
            ) : (
              <div className="flex items-center justify-center h-[450px] text-muted-foreground">
                {records ? "No data for selected range" : "Loading..."}
              </div>
            )
          ) : (
            <div className="overflow-x-auto">
              {tableRecords.length > 0 ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-3 text-xs font-medium text-muted-foreground">Date</th>
                      <th className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">Value</th>
                      {tableRecords[0]?.data &&
                        Object.keys(tableRecords[0].data).length > 0 && (
                          <th className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">Extra</th>
                        )}
                      <th className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRecords.map((r) => (
                      <tr key={r.id} className="border-b last:border-0 hover:bg-muted/50">
                        <td className="py-2 px-3 font-mono">{r.date}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatValue(r.value)}</td>
                        {r.data && Object.keys(r.data).length > 0 ? (
                          <td className="py-2 px-3 text-right text-xs text-muted-foreground">
                            {Object.entries(r.data)
                              .map(([k, v]) => `${k}: ${typeof v === "number" ? v.toFixed(2) : v}`)
                              .join(", ")}
                          </td>
                        ) : (
                          <td className="py-2 px-3 text-right text-muted-foreground">—</td>
                        )}
                        <td className="py-2 px-3 text-right text-xs text-muted-foreground">{r.data_source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">Loading...</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
