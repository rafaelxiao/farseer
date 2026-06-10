import { useMemo } from "react"
import type { OHLC } from "@/types"

interface OHLCDataTableProps {
  data: OHLC[]
}

export default function OHLCDataTable({ data }: OHLCDataTableProps) {
  const tableData = useMemo(() => {
    return [...data].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
  }, [data])

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] text-muted-foreground">
        No data to display
      </div>
    )
  }

  return (
    <div className="overflow-auto max-h-[500px]">
      <table className="w-full text-xs">
        <thead className="sticky top-0 bg-background z-10">
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
          {tableData.map((d, i) => {
            const next = i < tableData.length - 1 ? tableData[i + 1] : null
            const change = next ? ((d.close - next.close) / next.close * 100) : 0
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
                  {next ? `${isUp ? '+' : ''}${change.toFixed(2)}%` : '-'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
