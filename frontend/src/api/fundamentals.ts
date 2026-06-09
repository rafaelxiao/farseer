import { api } from "./client"
import type { Fundamentals } from "@/types"

export interface FundamentalsQueryParams {
  symbol?: string
  sector?: string
  start_date?: string
  end_date?: string
  limit?: number
}

export const fundamentalsApi = {
  get: (params?: FundamentalsQueryParams) => {
    const searchParams = new URLSearchParams()
    if (params?.symbol) searchParams.set("symbol", params.symbol)
    if (params?.sector) searchParams.set("sector", params.sector)
    if (params?.start_date) searchParams.set("start_date", params.start_date)
    if (params?.end_date) searchParams.set("end_date", params.end_date)
    if (params?.limit) searchParams.set("limit", String(params.limit))
    return api.get<Fundamentals[]>(`/fundamentals/?${searchParams}`)
  },

  create: (data: Omit<Fundamentals, "id" | "created_at" | "updated_at">) =>
    api.post<Fundamentals>("/fundamentals/", data),
}
