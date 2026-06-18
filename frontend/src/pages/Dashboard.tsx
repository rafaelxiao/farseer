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

export default function Dashboard() {
  const { data: symbols } = useQuery<SymbolInfo[]>({
    queryKey: ["symbols"],
    queryFn: () => api.get("/ohlc/symbols"),
  })

  const { data: jobs } = useQuery<TaskJob[]>({
    queryKey: ["jobs"],
    queryFn: () => api.get("/tasks/jobs"),
  })

  const { data: runs } = useQuery<TaskRun[]>({
    queryKey: ["task-runs"],
    queryFn: () => api.get("/tasks/?limit=5"),
  })

  // Calculate stats
  const totalSymbols = symbols?.length ?? 0
  const totalRecords = symbols?.reduce((sum, s) => sum + s.records, 0) ?? 0
  const latestDate = symbols?.length 
    ? symbols.reduce((latest, s) => s.latest > latest ? s.latest : latest, symbols[0].latest)
    : null

  // Count by exchange
  const shCount = symbols?.filter(s => s.symbol.endsWith(".SH")).length ?? 0
  const szCount = symbols?.filter(s => s.symbol.endsWith(".SZ")).length ?? 0
  const etfCount = symbols?.filter(s => {
    const code = s.symbol.split(".")[0]
    return (code.startsWith("51") || code.startsWith("58") || code.startsWith("15")) && code.length === 6
  }).length ?? 0
  const stockCount = totalSymbols - etfCount

  const formatNumber = (n: number) => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
    return n.toString()
  }

  const formatBytes = (mb: number) => {
    if (mb >= 1000) return `${(mb / 1000).toFixed(1)} GB`
    return `${mb} MB`
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
  const lastFetch = jobs?.[0]?.last_run
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
              {formatNumber(stockCount)} stocks · {formatNumber(etfCount)} ETFs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Records</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalRecords)}</div>
            <p className="text-xs text-muted-foreground">
              {formatBytes(Math.round(totalRecords * 0.0003))} estimated
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Latest Data</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestDate ? new Date(latestDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : "—"}
            </div>
            <p className="text-xs text-muted-foreground">
              {latestDate ? new Date(latestDate).toLocaleDateString('en-US', { weekday: 'long' }) : "No data"}
            </p>
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

      {/* Main Content Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Exchange Coverage */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Exchange Coverage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <span className="text-sm font-bold text-blue-700">SH</span>
                  </div>
                  <div>
                    <div className="font-medium">Shanghai</div>
                    <div className="text-sm text-muted-foreground">SSE</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold">{shCount}</div>
                  <div className="text-xs text-muted-foreground">symbols</div>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                    <span className="text-sm font-bold text-green-700">SZ</span>
                  </div>
                  <div>
                    <div className="font-medium">Shenzhen</div>
                    <div className="text-sm text-muted-foreground">SZSE</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold">{szCount}</div>
                  <div className="text-xs text-muted-foreground">symbols</div>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                    <span className="text-sm font-bold text-purple-700">ETF</span>
                  </div>
                  <div>
                    <div className="font-medium">ETFs</div>
                    <div className="text-sm text-muted-foreground">Funds</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold">{etfCount}</div>
                  <div className="text-xs text-muted-foreground">funds</div>
                </div>
              </div>
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
                    <div className="text-xs text-muted-foreground">
                      {run.finished_at && run.started_at
                        ? `${Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 60000)}m`
                        : "—"}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No recent activity</p>
            )}
          </CardContent>
        </Card>
      </div>

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
            <a href="/farseer/dev/docs" target="_blank" rel="noopener noreferrer" className="group">
              <div className="p-4 rounded-lg border bg-card hover:bg-accent transition-colors">
                <div className="font-medium group-hover:text-primary">API Docs</div>
                <div className="text-sm text-muted-foreground">Swagger UI</div>
              </div>
            </a>
          </div>
        </CardContent>
      </Card>

      {/* Data Sources */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Data Sources</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { name: "Tushare", status: "active", desc: "A-shares & ETFs" },
              { name: "AKShare", status: "available", desc: "Alternative source" },
              { name: "Baostock", status: "available", desc: "Free A-share data" },
              { name: "Yahoo Finance", status: "available", desc: "Global markets" },
              { name: "Binance", status: "available", desc: "Crypto data" },
            ].map((source) => (
              <div key={source.name} className="p-3 rounded-lg border">
                <div className="flex items-center gap-2 mb-1">
                  <div className={`w-2 h-2 rounded-full ${source.status === 'active' ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <span className="font-medium text-sm">{source.name}</span>
                </div>
                <div className="text-xs text-muted-foreground">{source.desc}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
