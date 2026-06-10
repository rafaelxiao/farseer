import { api } from "./client"
import type { OHLC } from "@/types"

export interface OHLCQueryParams {
  symbol: string
  timeframe?: string
  start?: string
  end?: string
  limit?: number
  adjust?: string
}

export const ohlcApi = {
  get: (params: OHLCQueryParams) => {
    const searchParams = new URLSearchParams({ symbol: params.symbol })
    if (params.timeframe) searchParams.set("timeframe", params.timeframe)
    if (params.start) searchParams.set("start", params.start)
    if (params.end) searchParams.set("end", params.end)
    if (params.limit) searchParams.set("limit", String(params.limit))
    if (params.adjust) searchParams.set("adjust", params.adjust)
    return api.get<OHLC[]>(`/ohlc/?${searchParams}`)
  },

  create: (data: Omit<OHLC, "id" | "created_at" | "updated_at">) =>
    api.post<OHLC>("/ohlc/", data),

  batchCreate: (items: Omit<OHLC, "id" | "created_at" | "updated_at">[]) =>
    api.post<OHLC[]>("/ohlc/batch", { items }),
}
