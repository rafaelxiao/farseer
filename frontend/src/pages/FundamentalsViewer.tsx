import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fundamentalsApi, type FundamentalPeriod } from "@/api/fundamentals"
import SymbolSearch from "@/components/shared/SymbolSearch"
import FundamentalChart from "@/components/shared/FundamentalChart"

const STOCK_CATEGORIES = [
  { key: "income", label: "Income", icon: "💰" },
  { key: "balance_sheet", label: "Balance Sheet", icon: "📊" },
  { key: "financial_indicator", label: "Indicators", icon: "📈" },
  { key: "valuation", label: "Valuation", icon: "💎" },
]

const CHARTABLE_METRICS = [
  { key: "roe", label: "ROE (%)", color: "#22c55e" },
  { key: "roa", label: "ROA (%)", color: "#3b82f6" },
  { key: "net_margin", label: "Net Margin (%)", color: "#f59e0b" },
  { key: "gross_margin", label: "Gross Margin (%)", color: "#8b5cf6" },
  { key: "eps", label: "EPS", color: "#ef4444" },
  { key: "debt_to_assets", label: "Debt/Assets (%)", color: "#6366f1" },
  { key: "revenue_yoy", label: "Revenue YoY (%)", color: "#06b6d4" },
  { key: "net_income_yoy", label: "Profit YoY (%)", color: "#ec4899" },
]

const INCOME_METRICS = [
  { key: "revenue", label: "Revenue", color: "#3b82f6" },
  { key: "net_income_attr_p", label: "Net Profit", color: "#22c55e" },
  { key: "basic_eps", label: "EPS", color: "#f59e0b" },
]

const BALANCE_METRICS = [
  { key: "total_assets", label: "Total Assets", color: "#3b82f6" },
  { key: "total_liab", label: "Total Liabilities", color: "#ef4444" },
  { key: "equity", label: "Equity", color: "#22c55e" },
]

const VALUATION_METRICS = [
  { key: "pe", label: "P/E", color: "#3b82f6" },
  { key: "pb", label: "P/B", color: "#22c55e" },
  { key: "ps", label: "P/S", color: "#f59e0b" },
  { key: "dividend_yield", label: "Div Yield %", color: "#8b5cf6" },
]

type AssetType = "stock" | "etf"

function isETF(symbol: string): boolean {
  const code = symbol.split(".")[0]
  return (
    (code.startsWith("51") || code.startsWith("58") || code.startsWith("15")) &&
    code.length === 6
  )
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-"
  if (Math.abs(value) >= 1e12) return `${(value / 1e12).toFixed(2)}T`
  if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(2)}B`
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(2)}M`
  if (Math.abs(value) >= 1e3) return `${(value / 1e3).toFixed(2)}K`
  return value.toFixed(2)
}

function formatQuarter(dateStr: string): string {
  if (!dateStr) return "-"
  if (dateStr.length === 8) {
    const year = dateStr.slice(0, 4)
    const month = dateStr.slice(4, 6)
    const quarter = Math.ceil(parseInt(month) / 3)
    return `${year}-Q${quarter}`
  }
  return dateStr
}

export default function FundamentalsViewer() {
  const [symbol, setSymbol] = useState("000001.SZ")
  const [assetType, setAssetType] = useState<AssetType>("stock")
  const [activeTab, setActiveTab] = useState("income")
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart")
  const [startDate, setStartDate] = useState(() => {
    const d = new Date()
    d.setFullYear(d.getFullYear() - 3)
    return d.toISOString().split("T")[0]
  })
  const [endDate, setEndDate] = useState("")
  const [selectedMetric, setSelectedMetric] = useState("revenue")

  // Auto-detect asset type when symbol changes
  const handleSymbolChange = (newSymbol: string) => {
    setSymbol(newSymbol)
    setAssetType(isETF(newSymbol) ? "etf" : "stock")
    setActiveTab(isETF(newSymbol) ? "nav" : "income")
  }

  // Handle tab switch with default symbol
  const handleAssetTypeChange = (type: AssetType) => {
    setAssetType(type)
    if (type === "etf") {
      setSymbol("510050.SH")
      setActiveTab("nav")
    } else {
      setSymbol("000001.SZ")
      setActiveTab("income")
    }
  }

  const { data: summary } = useQuery({
    queryKey: ["fundamental-summary", symbol, startDate, endDate],
    queryFn: () => fundamentalsApi.getSummary(symbol, startDate || undefined, endDate || undefined),
    enabled: !!symbol,
  })

  const { data: valuationHistory } = useQuery({
    queryKey: ["valuation-history", symbol, startDate, endDate],
    queryFn: () => fundamentalsApi.getValuationHistory(symbol, startDate || undefined, endDate || undefined),
    enabled: !!symbol && assetType === "stock" && activeTab === "valuation",
  })

  const { data: etfNavHistory } = useQuery({
    queryKey: ["etf-nav-history", symbol, startDate, endDate],
    queryFn: () => fundamentalsApi.getETFNavHistory(symbol, startDate || undefined, endDate || undefined),
    enabled: !!symbol && assetType === "etf",
  })

  const allData = useMemo(() => {
    if (!summary?.categories) return {} as any
    return summary.categories as any
  }, [summary])

  const chartMetrics = useMemo(() => {
    if (activeTab === "income") return INCOME_METRICS
    if (activeTab === "balance_sheet") return BALANCE_METRICS
    if (activeTab === "financial_indicator") return CHARTABLE_METRICS
    if (activeTab === "valuation") return VALUATION_METRICS
    return []
  }, [activeTab])

  const categoryData = useMemo(() => {
    return (allData[activeTab] || []) as FundamentalPeriod[]
  }, [allData, activeTab])

  return (
    <div className="w-full max-w-6xl mx-auto space-y-4">
      {/* Header with Symbol Search and Asset Type Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">Fundamentals</h1>
          <div className="flex border rounded">
            <button
              className={`px-3 py-1.5 text-sm ${
                assetType === "stock"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent"
              }`}
              onClick={() => handleAssetTypeChange("stock")}
            >
              Stock
            </button>
            <button
              className={`px-3 py-1.5 text-sm ${
                assetType === "etf"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent"
              }`}
              onClick={() => handleAssetTypeChange("etf")}
            >
              ETF
            </button>
          </div>
        </div>
        <SymbolSearch value={symbol} onSelect={handleSymbolChange} assetType={assetType} />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{symbol}</Badge>
            <Badge variant="secondary">{assetType === "etf" ? "ETF" : "Stock"}</Badge>

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

            <div className="flex border rounded">
              <button
                className={`px-2 py-1 text-xs ${
                  viewMode === "chart" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                }`}
                onClick={() => setViewMode("chart")}
              >
                Chart
              </button>
              <button
                className={`px-2 py-1 text-xs ${
                  viewMode === "table" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                }`}
                onClick={() => setViewMode("table")}
              >
                Table
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* STOCK VIEW */}
      {assetType === "stock" && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {(() => {
              const income = allData.income?.[0]?.data || {}
              const indicator = allData.financial_indicator?.[0]?.data || {}
              const val = allData.valuation?.[0]?.data || {}
              return [
                { label: "Revenue", value: formatNumber(income.revenue) },
                { label: "Net Profit", value: formatNumber(income.net_income_attr_p) },
                { label: "EPS", value: income.basic_eps?.toFixed(2) || "-" },
                { label: "ROE", value: indicator.roe ? `${indicator.roe.toFixed(2)}%` : "-" },
                { label: "P/E", value: val.pe?.toFixed(2) || "-" },
                { label: "P/B", value: val.pb?.toFixed(2) || "-" },
              ].map((m, i) => (
                <div key={i} className="p-3 rounded-lg border bg-card">
                  <div className="text-xs text-muted-foreground mb-1">{m.label}</div>
                  <div className="text-lg font-semibold">{m.value}</div>
                </div>
              ))
            })()}
          </div>

          {/* Category Tabs + Content */}
          <Card>
            <CardHeader className="py-3">
              <div className="flex items-center justify-between">
                <div className="flex gap-1 border-b pb-2">
                  {STOCK_CATEGORIES.map((cat) => (
                    <button
                      key={cat.key}
                      className={`px-3 py-1.5 text-sm rounded-t-md transition-colors ${
                        activeTab === cat.key
                          ? "bg-primary text-primary-foreground font-medium"
                          : "text-muted-foreground hover:bg-accent"
                      }`}
                      onClick={() => {
                        setActiveTab(cat.key)
                        const defaults: Record<string, string> = {
                          income: "revenue",
                          balance_sheet: "total_assets",
                          financial_indicator: "roe",
                          valuation: "pe",
                        }
                        setSelectedMetric(defaults[cat.key] || "revenue")
                      }}
                    >
                      {cat.icon} {cat.label}
                    </button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {viewMode === "chart" ? (
                <div className="space-y-4">
                  {/* Metric selector (not for valuation) */}
                  {activeTab !== "valuation" && chartMetrics.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {chartMetrics.map((m) => (
                        <button
                          key={m.key}
                          onClick={() => setSelectedMetric(m.key)}
                          className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                            selectedMetric === m.key
                              ? "bg-primary text-primary-foreground border-primary"
                              : "text-muted-foreground hover:bg-accent"
                          }`}
                        >
                          {m.label}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Chart */}
                  {activeTab === "valuation" && valuationHistory ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {["pe", "pb", "ps", "peg"].map((metric) => {
                        const data = valuationHistory.data.filter((d: any) => d[metric])
                        if (data.length === 0) return null
                        return (
                          <Card key={metric}>
                            <CardHeader className="py-2">
                              <CardTitle className="text-sm">{metric.toUpperCase()}</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <FundamentalChart
                                data={data.map((d: any) => ({
                                  date: d.date.replace(/-/g, ""),
                                  data: { [metric]: d[metric] },
                                }))}
                                metricKey={metric}
                                label={metric.toUpperCase()}
                                height={250}
                                color={chartMetrics.find((m) => m.key === metric)?.color || "#3b82f6"}
                              />
                            </CardContent>
                          </Card>
                        )
                      })}
                    </div>
                  ) : categoryData.length > 0 ? (
                    <FundamentalChart
                      data={categoryData}
                      metricKey={selectedMetric}
                      label={chartMetrics.find((m) => m.key === selectedMetric)?.label || selectedMetric}
                      height={400}
                      color={chartMetrics.find((m) => m.key === selectedMetric)?.color || "#3b82f6"}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                      No data to display
                    </div>
                  )}
                </div>
              ) : (
                /* Table View */
                <div className="overflow-x-auto">
                  {categoryData.length > 0 ? (
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-3 text-xs font-medium text-muted-foreground">Period</th>
                          {Object.keys(categoryData[0]?.data || {}).slice(0, 10).map((key) => (
                            <th key={key} className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">
                              {key.replace(/_/g, " ")}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {categoryData.map((period, i) => (
                          <tr key={i} className="border-b last:border-0 hover:bg-muted/50">
                            <td className="py-2 px-3 font-mono">{formatQuarter(period.date)}</td>
                            {Object.values(period.data).slice(0, 10).map((val: any, j) => (
                              <td key={j} className="py-2 px-3 text-right">
                                {typeof val === "number" ? formatNumber(val) : val ?? "-"}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">No data available</div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* ETF VIEW */}
      {assetType === "etf" && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {(() => {
              const nav = allData.etf_nav?.[0]?.data || {}
              const info = allData.etf_info?.[0]?.data || {}
              const basic = allData.etf_basic?.[0]?.data || {}
              return [
                { label: "NAV", value: nav.unit_nav?.toFixed(4) || "-" },
                { label: "IOPV", value: info.IOPV?.toFixed(4) || "-" },
                { label: "Premium", value: info.折价率 !== undefined ? `${info.折价率}%` : "-" },
                { label: "AUM", value: info.总市值 ? `${(info.总市值 / 1e8).toFixed(0)}亿` : "-" },
                { label: "Turnover", value: info.换手率 ? `${info.换手率}%` : "-" },
                { label: "Fee", value: basic.m_fee ? `${basic.m_fee}%` : "-" },
              ].map((m, i) => (
                <div key={i} className="p-3 rounded-lg border bg-card">
                  <div className="text-xs text-muted-foreground mb-1">{m.label}</div>
                  <div className="text-lg font-semibold">{m.value}</div>
                </div>
              ))
            })()}
          </div>

          {/* ETF Content */}
          <Card>
            <CardHeader className="py-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{symbol} ETF</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              {viewMode === "chart" ? (
                /* Chart View */
                etfNavHistory && etfNavHistory.data.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="py-2">
                        <CardTitle className="text-sm">Price & NAV</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <FundamentalChart
                          data={etfNavHistory.data
                            .filter((d) => d.nav)
                            .map((d) => ({
                              date: d.date.replace(/-/g, ""),
                              data: { nav: d.nav! },
                            }))}
                          metricKey="nav"
                          label="NAV"
                          height={300}
                          color="#3b82f6"
                        />
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="py-2">
                        <CardTitle className="text-sm">Premium/Discount %</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <FundamentalChart
                          data={etfNavHistory.data
                            .filter((d) => d.premium !== undefined)
                            .map((d) => ({
                              date: d.date.replace(/-/g, ""),
                              data: { premium: d.premium! },
                            }))}
                          metricKey="premium"
                          label="Premium %"
                          height={300}
                          color="#22c55e"
                        />
                        <div className="text-xs text-muted-foreground text-center mt-2">
                          Positive = Overvalue | Negative = Undervalue
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">Loading NAV history...</div>
                )
              ) : (
                /* Table View */
                etfNavHistory && etfNavHistory.data.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-3 text-xs font-medium text-muted-foreground">Date</th>
                          <th className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">NAV</th>
                          <th className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">Price</th>
                          <th className="text-right py-2 px-3 text-xs font-medium text-muted-foreground">Premium %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {etfNavHistory.data.slice(-50).reverse().map((row, i) => (
                          <tr key={i} className="border-b last:border-0 hover:bg-muted/50">
                            <td className="py-2 px-3 font-mono">{row.date}</td>
                            <td className="py-2 px-3 text-right">{row.nav?.toFixed(4) ?? "-"}</td>
                            <td className="py-2 px-3 text-right">{row.price?.toFixed(3) ?? "-"}</td>
                            <td
                              className={`py-2 px-3 text-right ${
                                row.premium !== undefined
                                  ? row.premium > 0
                                    ? "text-red-600"
                                    : row.premium < 0
                                    ? "text-green-600"
                                    : ""
                                  : ""
                              }`}
                            >
                              {row.premium !== undefined
                                ? `${row.premium > 0 ? "+" : ""}${row.premium.toFixed(2)}%`
                                : "-"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {etfNavHistory.data.length > 50 && (
                      <div className="text-xs text-muted-foreground text-center mt-2">
                        Showing last 50 of {etfNavHistory.data.length} records
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">No data available</div>
                )
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
