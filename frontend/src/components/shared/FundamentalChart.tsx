import { useEffect, useRef } from "react"
import { createChart, ColorType, LineSeries } from "lightweight-charts"
import type { FundamentalPeriod } from "@/api/fundamentals"

interface FundamentalChartProps {
  data: FundamentalPeriod[]
  metricKey: string
  label: string
  height?: number
  color?: string
}

export default function FundamentalChart({ 
  data, 
  metricKey, 
  label, 
  height = 300,
  color = "#3b82f6"
}: FundamentalChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return

    // Clear previous chart
    chartContainerRef.current.innerHTML = ""

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: "#333",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "#f0f0f0" },
        horzLines: { color: "#f0f0f0" },
      },
      rightPriceScale: {
        borderColor: "#d1d5db",
      },
      timeScale: {
        borderColor: "#d1d5db",
        timeVisible: false,
      },
      height,
    })

    // Prepare data - sort by date ascending
    const sorted = [...data]
      .filter(d => d.data[metricKey] !== null && d.data[metricKey] !== undefined)
      .sort((a, b) => a.date.localeCompare(b.date))

    if (sorted.length === 0) {
      chartContainerRef.current.innerHTML = `
        <div class="flex items-center justify-center h-full text-muted-foreground">
          No data for ${label}
        </div>
      `
      return
    }

    // Format large numbers on Y-axis
    const formatPrice = (price: number) => {
      if (Math.abs(price) >= 1e12) return `${(price / 1e12).toFixed(1)}T`
      if (Math.abs(price) >= 1e9) return `${(price / 1e9).toFixed(1)}B`
      if (Math.abs(price) >= 1e6) return `${(price / 1e6).toFixed(1)}M`
      if (Math.abs(price) >= 1e3) return `${(price / 1e3).toFixed(1)}K`
      return price.toFixed(2)
    }

    // Create line series
    const lineSeries = chart.addSeries(LineSeries, {
      color,
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      priceFormat: {
        type: 'custom',
        formatter: formatPrice,
      },
    })

    // Set data - convert YYYYMMDD to YYYY-MM-DD format
    lineSeries.setData(
      sorted.map((d) => {
        // Handle both YYYYMMDD and YYYY-MM-DD formats
        let dateStr = d.date
        if (dateStr.length === 8 && !dateStr.includes("-")) {
          dateStr = `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`
        }
        return {
          time: dateStr as any,
          value: d.data[metricKey],
        }
      })
    )

    // Add area fill
    lineSeries.applyOptions({
      lastValueVisible: true,
      priceLineVisible: true,
    })

    chart.timeScale().fitContent()

    return () => {
      chart.remove()
    }
  }, [data, metricKey, label, height, color])

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground">
        No data to display
      </div>
    )
  }

  return <div ref={chartContainerRef} />
}
