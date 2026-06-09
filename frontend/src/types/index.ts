export interface OHLC {
  id: number
  symbol: string
  timeframe: string
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  created_at: string
  updated_at: string
}

export interface Fundamentals {
  id: number
  symbol: string
  date: string
  pe_ratio: number | null
  pb_ratio: number | null
  market_cap: number | null
  revenue: number | null
  net_income: number | null
  eps: number | null
  dividend_yield: number | null
  sector: string | null
  industry: string | null
  extra: string | null
  created_at: string
  updated_at: string
}

export interface TaskRun {
  id: number
  job_id: string
  status: "pending" | "running" | "success" | "failed"
  started_at: string | null
  finished_at: string | null
  result: string | null
  created_at: string
}

export interface TaskJob {
  job_id: string
  last_run: string | null
  last_status: string | null
  next_run: string | null
  total_runs: number
}
