import { api } from "./client"

export interface MacroRecord {
  id: number
  symbol: string
  data_source: string
  date: string
  value: number
  data: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface MacroSymbol {
  symbol: string
  data_source: string
}

export const macroApi = {
  listSymbols: () => api.get<MacroSymbol[]>("/macro/symbols"),

  query: (
    symbol?: string,
    startDate?: string,
    endDate?: string,
    limit?: number,
  ) => {
    const params = new URLSearchParams()
    if (symbol) params.set("symbol", symbol)
    if (startDate) params.set("start_date", startDate)
    if (endDate) params.set("end_date", endDate)
    if (limit) params.set("limit", String(limit))
    return api.get<MacroRecord[]>(`/macro/?${params}`)
  },
}
