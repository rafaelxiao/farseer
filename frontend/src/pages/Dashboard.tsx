import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { api } from "@/api/client"
import { Link } from "react-router-dom"

interface SymbolInfo {
  symbol: string
  records: number
  latest: string
}

interface TaskJob {
  job_id: string
  last_status: string | null
  last_run: string | null
  next_run: string | null
  total_runs: number
}

interface TaskRun {
  id: number
  job_id: string
  status: string
  started_at: string | null
  finished_at: string | null
  result: string | null
}

interface MacroInfo {
  symbol: string
  data_source: string
  records: number
  from_date: string
  to_date: string
}

const DATA_SOURCES = [
  { key: "akshare", label: "AKShare" },
  { key: "tushare", label: "Tushare" },
]

const DAILY_TASKS = [
  { step: "1", what: "OHLC Stocks", source: "Sina raw", freq: "Daily", time: "~0s (skips if current)" },
  { step: "2", what: "OHLC ETFs", source: "Sina", freq: "Daily", time: "~0s (skips if current)" },
  { step: "3", what: "OHLC Indices", source: "AKShare", freq: "Daily", time: "~45s" },
  { step: "4", what: "Fundamentals", source: "AKShare", freq: "Daily", time: "~4 min" },
  { step: "5", what: "Macro", source: "AKShare", freq: "Daily", time: "~5s" },
  { step: "6", what: "BF Sweep", source: "Sina hfq", freq: "Friday only", time: "~1h (split detection)" },
  { step: "7", what: "ETF Sweep", source: "Sina", freq: "Friday only", time: "~5 min (split refetch)" },
]

export default function Dashboard() {
  // Fetch symbols per data source
  const queries = DATA_SOURCES.map(src =>
    useQuery<SymbolInfo[]>({
      queryKey: ["symbols", src.key],
      queryFn: () => api.get(`/ohlc/symbols?data_source=${src.key}`),
      enabled: true,
    })
  )

  const { data: jobs } = useQuery<TaskJob[]>({
    queryKey: ["jobs"],
    queryFn: () => api.get("/tasks/jobs"),
  })

  const { data: runs } = useQuery<TaskRun[]>({
    queryKey: ["task-runs"],
    queryFn: () => api.get("/tasks/?limit=5"),
  })

  const { data: macroSymbols } = useQuery<MacroInfo[]>({
    queryKey: ["macro-symbols"],
    queryFn: () => api.get("/macro/symbols"),
  })

  // Symbol counts per source
  const symbolCounts = DATA_SOURCES.map((src, i) => {
    const d = queries[i].data
    return {
      source: src.label,
      count: d?.length ?? 0,
      records: d?.reduce((sum, s) => sum + s.records, 0) ?? 0,
      from: d?.length ? d.reduce((min, s) => s.latest < min ? s.latest : min, d[0].latest) : null,
      to: d?.length ? d.reduce((max, s) => s.latest > max ? s.latest : max, d[0].latest) : null,
    }
  })

  // Build inventory from combined data
  const inventory = [
    ...DATA_SOURCES.map((src, i) => {
      const d = queries[i].data ?? []
      const stocks = d.filter(s => {
        const code = s.symbol.split(".")[0]
        return !(code.startsWith("0000") && s.symbol.endsWith(".SH")) // exclude indices
          && !(code.startsWith("1") || code.startsWith("5")) // exclude ETFs
          && !["399001","399005","399006","399673","399101","399330","931566","931612","932000","931575","980017"].includes(code)
      })
      const records = stocks.reduce((sum, s) => sum + s.records, 0)
      const fromDate = stocks.length ? stocks.reduce((min, s) => s.latest < min ? s.latest : min, stocks[0].latest) : null
      const toDate = stocks.length ? stocks.reduce((max, s) => s.latest > max ? s.latest : max, stocks[0].latest) : null
      return {
        type: "OHLC Stocks",
        source: src.label,
        records,
        symbols: stocks.length,
        from: fromDate,
        to: toDate,
      }
    }),
    // ETFs - from AKShare source
    ...(() => {
      const akData = queries[0].data ?? []
      const etfs = akData.filter(s => {
        const code = s.symbol.split(".")[0]
        return (code.startsWith("1") || code.startsWith("5")) && code.length === 6
      })
      if (etfs.length === 0) {
        // Fallback to Tushare
        const tsData = queries[1].data ?? []
        const tsEtfs = tsData.filter(s => {
          const code = s.symbol.split(".")[0]
          return (code.startsWith("1") || code.startsWith("5")) && code.length === 6
        })
        return [{
          type: "OHLC ETFs", source: "Tushare",
          records: tsEtfs.reduce((sum, s) => sum + s.records, 0),
          symbols: tsEtfs.length,
          from: tsEtfs.length ? tsEtfs.reduce((min, s) => s.latest < min ? s.latest : min, tsEtfs[0].latest) : null,
          to: tsEtfs.length ? tsEtfs.reduce((max, s) => s.latest > max ? s.latest : max, tsEtfs[0].latest) : null,
        }]
      }
      return [{
        type: "OHLC ETFs", source: "AKShare",
        records: etfs.reduce((sum, s) => sum + s.records, 0),
        symbols: etfs.length,
        from: etfs.length ? etfs.reduce((min, s) => s.latest < min ? s.latest : min, etfs[0].latest) : null,
        to: etfs.length ? etfs.reduce((max, s) => s.latest > max ? s.latest : max, etfs[0].latest) : null,
      }]
    })(),
    // Indices
    ...(() => {
      const akData = queries[0].data ?? []
      const indexCodes = ["000001","000016","000300","000688","000852","000905","399001","399005","399006","399673","931566","931612","932000","931575","980017"]
      const indices = akData.filter(s => indexCodes.includes(s.symbol.split(".")[0]))
      return [{
        type: "OHLC Indices",
        source: "AKShare",
        records: indices.reduce((sum, s) => sum + s.records, 0),
        symbols: indices.length,
        from: indices.length ? indices.reduce((min, s) => s.latest < min ? s.latest : min, indices[0].latest) : null,
        to: indices.length ? indices.reduce((max, s) => s.latest > max ? s.latest : max, indices[0].latest) : null,
      }]
    })(),
    // Fundamentals
    {
      type: "Fundamentals",
      source: "AKShare",
      records: 91788,
      symbols: 1216,
      from: "1988-12-31",
      to: "2026-03-31",
    },
    {
      type: "Fundamentals",
      source: "Tushare",
      records: 40050,
      symbols: 1304,
      from: "2017-12-31",
      to: "2026-06-12",
    },
    // Macro
    {
      type: "Macro",
      source: "AKShare",
      records: macroSymbols?.reduce((sum, m) => sum + m.records, 0) ?? 17416,
      symbols: macroSymbols?.length ?? 22,
      from: "1970-01-01",
      to: "2026-06-29",
    },
  ]

  // Overall stats
  const totalSymbols = symbolCounts.reduce((sum, s) => sum + s.count, 0)
  const totalRecords = symbolCounts.reduce((sum, s) => sum + s.records, 0)
  const latestDate = symbolCounts
    .filter(s => s.to)
    .reduce((max, s) => (s.to! > max ? s.to! : max), "2000-01-01")

  const formatNumber = (n: number) => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
    return n.toString()
  }

  const fmtDate = (d: string | null) => {
    if (!d) return "—"
    // API returns ISO timestamps like "2026-06-25T16:00:00+00:00" — keep just the date
    return d.slice(0, 10)
  }

  const statusVariant = (status: string) => {
    switch (status) {
      case "success": return "success"
      case "failed": return "destructive"
      case "running": return "warning"
      case "skipped": return "secondary"
      default: return "secondary"
    }
  }

  const nextFetch = jobs?.[0]?.next_run
  const lastStatus = jobs?.[0]?.last_status

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Farseer Dashboard</h1>
          <p className="text-sm text-muted-foreground">Market data management system</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={lastStatus === "success" ? "success" : lastStatus === "skipped" ? "secondary" : "destructive"}>
            Last fetch: {lastStatus ?? "never"}
          </Badge>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Symbols</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalSymbols)}</div>
            <p className="text-xs text-muted-foreground">
              {symbolCounts.map(s => `${s.source}: ${s.count}`).join(' · ')}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Records</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalRecords)}</div>
            <p className="text-xs text-muted-foreground">~3.5 GB</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Latest Data</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{fmtDate(latestDate)}</div>
            <p className="text-xs text-muted-foreground">AKShare OHLC</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Next Fetch</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {nextFetch
                ? new Date(nextFetch).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
                : "—"}
            </div>
            <p className="text-xs text-muted-foreground">
              {nextFetch ? new Date(nextFetch).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : "Not scheduled"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Data Inventory */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Data Inventory</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Type</th>
                  <th className="pb-2 font-medium">Source</th>
                  <th className="pb-2 font-medium text-right">Records</th>
                  <th className="pb-2 font-medium text-right">Symbols</th>
                  <th className="pb-2 font-medium">From</th>
                  <th className="pb-2 font-medium">To</th>
                </tr>
              </thead>
              <tbody>
                {inventory.filter(row => row.records > 0).map((row, i) => (
                  <tr key={i} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="py-2">{row.type}</td>
                    <td className="py-2">
                      <Badge variant="secondary" className="text-xs">{row.source}</Badge>
                    </td>
                    <td className="py-2 text-right font-mono">{formatNumber(row.records)}</td>
                    <td className="py-2 text-right font-mono">{row.symbols}</td>
                    <td className="py-2 font-mono text-xs">{fmtDate(row.from)}</td>
                    <td className="py-2 font-mono text-xs">{fmtDate(row.to)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Daily Tasks */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Daily Task Schedule (18:00 CST)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium w-8">#</th>
                  <th className="pb-2 font-medium">Task</th>
                  <th className="pb-2 font-medium">Source</th>
                  <th className="pb-2 font-medium">Freq</th>
                  <th className="pb-2 font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {DAILY_TASKS.map((task) => (
                  <tr key={task.step} className={`border-b last:border-0 hover:bg-muted/50 ${task.freq === "Skipped" ? "text-muted-foreground" : ""}`}>
                    <td className="py-2">{task.step}</td>
                    <td className="py-2">{task.what}</td>
                    <td className="py-2">
                      <Badge variant="secondary" className="text-xs">{task.source}</Badge>
                    </td>
                    <td className="py-2">
                      <Badge variant={task.freq === "Skipped" ? "outline" : "success"} className="text-xs">
                        {task.freq}
                      </Badge>
                    </td>
                    <td className="py-2 text-xs text-muted-foreground">{task.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {runs && runs.length > 0 ? (
            <div className="space-y-3">
              {runs.slice(0, 5).map((run) => (
                <div key={run.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant={statusVariant(run.status)} className="w-16 justify-center">
                      {run.status}
                    </Badge>
                    <div>
                      <div className="text-sm font-medium">{run.job_id}</div>
                      <div className="text-xs text-muted-foreground">
                        {run.started_at ? new Date(run.started_at).toLocaleString() : "—"}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No recent activity</p>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link to="/ohlc" className="group">
              <div className="p-4 rounded-lg border bg-card hover:bg-accent transition-colors">
                <div className="font-medium group-hover:text-primary">OHLC Viewer</div>
                <div className="text-sm text-muted-foreground">Price charts & data</div>
              </div>
            </Link>
            <Link to="/fundamentals" className="group">
              <div className="p-4 rounded-lg border bg-card hover:bg-accent transition-colors">
                <div className="font-medium group-hover:text-primary">Fundamentals</div>
                <div className="text-sm text-muted-foreground">Financial data</div>
              </div>
            </Link>
            <Link to="/tasks" className="group">
              <div className="p-4 rounded-lg border bg-card hover:bg-accent transition-colors">
                <div className="font-medium group-hover:text-primary">Tasks</div>
                <div className="text-sm text-muted-foreground">Manage fetchers</div>
              </div>
            </Link>
            <a href="/farseer/docs" target="_blank" rel="noopener noreferrer" className="group">
              <div className="p-4 rounded-lg border bg-card hover:bg-accent transition-colors">
                <div className="font-medium group-hover:text-primary">API Docs</div>
                <div className="text-sm text-muted-foreground">Swagger UI</div>
              </div>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
