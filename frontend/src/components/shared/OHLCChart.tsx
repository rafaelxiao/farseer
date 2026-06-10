import { useMemo } from "react"
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import type { OHLC } from "@/types"

interface OHLCChartProps {
  data: OHLC[]
  height?: number
}

export default function OHLCChart({ data, height = 400 }: OHLCChartProps) {
  const chartData = useMemo(() => {
    return [...data]
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .map((d) => ({
        date: new Date(d.timestamp).toLocaleDateString(),
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
        isUp: d.close >= d.open,
      }))
  }, [data])

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] text-muted-foreground">
        No data to display
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* OHLC Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const d = payload[0].payload
              return (
                <div className="bg-white border rounded p-2 shadow text-xs">
                  <div className="font-medium">{d.date}</div>
                  <div>O: {d.open?.toFixed(2)}</div>
                  <div>H: {d.high?.toFixed(2)}</div>
                  <div>L: {d.low?.toFixed(2)}</div>
                  <div>C: {d.close?.toFixed(2)}</div>
                  <div>V: {d.volume?.toLocaleString()}</div>
                </div>
              )
            }}
          />
          <Bar
            dataKey="high"
            fill="transparent"
            stroke="transparent"
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Volume Chart */}
      <ResponsiveContainer width="100%" height={100}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={false} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const d = payload[0].payload
              return (
                <div className="bg-white border rounded p-2 shadow text-xs">
                  <div>{d.date}</div>
                  <div>Volume: {d.volume?.toLocaleString()}</div>
                </div>
              )
            }}
          />
          <Bar
            dataKey="volume"
            fill="#6b7280"
            opacity={0.5}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
