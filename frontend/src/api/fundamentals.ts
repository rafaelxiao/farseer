import { api } from "./client"
import type { Fundamentals } from "@/types"

export interface FundamentalsQueryParams {
  symbol?: string
  category?: string
  start_date?: string
  end_date?: string
  limit?: number
}

export interface FundamentalPeriod {
  date: string
  data: Record<string, any>
}

export interface FundamentalSummary {
  symbol: string
  categories: {
    [key: string]: FundamentalPeriod[]
  }
  available_dates: string[]
}

export interface ValuationHistory {
  symbol: string
  data: Array<{
    date: string
    price: number
    pe?: number
    pb?: number
    ps?: number
    peg?: number
  }>
}

export interface ETFNavHistory {
  symbol: string
  data: Array<{
    date: string
    nav?: number
    price?: number
    premium?: number
  }>
}

export const fundamentalsApi = {
  get: (params?: FundamentalsQueryParams) => {
    const searchParams = new URLSearchParams()
    if (params?.symbol) searchParams.set("symbol", params.symbol)
    if (params?.category) searchParams.set("category", params.category)
    if (params?.start_date) searchParams.set("start_date", params.start_date)
    if (params?.end_date) searchParams.set("end_date", params.end_date)
    if (params?.limit) searchParams.set("limit", String(params.limit))
    return api.get<Fundamentals[]>(`/fundamentals/?${searchParams}`)
  },

  getSummary: (symbol: string, startDate?: string, endDate?: string) => {
    const searchParams = new URLSearchParams()
    if (startDate) searchParams.set("start_date", startDate)
    if (endDate) searchParams.set("end_date", endDate)
    return api.get<FundamentalSummary>(`/fundamentals/summary/${symbol}?${searchParams}`)
  },

  create: (data: Omit<Fundamentals, "id" | "created_at" | "updated_at">) =>
    api.post<Fundamentals>("/fundamentals/", data),

  getValuationHistory: (symbol: string, startDate?: string, endDate?: string) => {
    const searchParams = new URLSearchParams()
    if (startDate) searchParams.set("start_date", startDate)
    if (endDate) searchParams.set("end_date", endDate)
    return api.get<ValuationHistory>(`/fundamentals/valuation-history/${symbol}?${searchParams}`)
  },

  getETFNavHistory: (symbol: string, startDate?: string, endDate?: string) => {
    const searchParams = new URLSearchParams()
    if (startDate) searchParams.set("start_date", startDate)
    if (endDate) searchParams.set("end_date", endDate)
    return api.get<ETFNavHistory>(`/fundamentals/etf-nav-history/${symbol}?${searchParams}`)
  },
}
