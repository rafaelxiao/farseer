import { useMemo } from "react"
import type { OHLC } from "@/types"

interface OHLCChartProps {
  data: OHLC[]
  height?: number
}

export default function OHLCChart({ data, height = 400 }: OHLCChartProps) {
  const chartData = useMemo(() => {
    return [...data]
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .slice(-100) // Show last 100 records for now
  }, [data])

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] text-muted-foreground">
        No data to display
      </div>
    )
  }

  // Simple table view for now
  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        Showing {chartData.length} of {data.length} records
      </div>
      
      <div className="overflow-auto max-h-[500px]">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-background">
            <tr className="border-b">
              <th className="text-left p-2">Date</th>
              <th className="text-right p-2">Open</th>
              <th className="text-right p-2">High</th>
              <th className="text-right p-2">Low</th>
              <th className="text-right p-2">Close</th>
              <th className="text-right p-2">Volume</th>
              <th className="text-right p-2">Change</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((d, i) => {
              const prev = i > 0 ? chartData[i - 1] : null
              const change = prev ? ((d.close - prev.close) / prev.close * 100) : 0
              const isUp = change >= 0
              
              return (
                <tr key={d.id} className="border-b hover:bg-muted/50">
                  <td className="p-2">
                    {new Date(d.timestamp).toLocaleDateString()}
                  </td>
                  <td className="text-right p-2">{d.open.toFixed(2)}</td>
                  <td className="text-right p-2">{d.high.toFixed(2)}</td>
                  <td className="text-right p-2">{d.low.toFixed(2)}</td>
                  <td className="text-right p-2 font-medium">{d.close.toFixed(2)}</td>
                  <td className="text-right p-2 text-muted-foreground">
                    {d.volume.toLocaleString()}
                  </td>
                  <td className={`text-right p-2 ${isUp ? 'text-red-600' : 'text-green-600'}`}>
                    {change !== 0 ? `${isUp ? '+' : ''}${change.toFixed(2)}%` : '-'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
