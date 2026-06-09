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
  adjusted_close: number | null
  split_factor: number | null
  dividend_amount: number | null
  data: Record<string, any>  // Extra: vwap, turnover, etc.
  created_at: string
  updated_at: string
}

export interface Fundamentals {
  id: number
  symbol: string
  date: string
  category: string | null
  data: Record<string, any>
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
