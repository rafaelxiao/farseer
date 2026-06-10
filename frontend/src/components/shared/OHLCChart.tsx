import { useEffect, useRef } from "react"
import { createChart, ColorType, CrosshairMode } from "lightweight-charts"
import type { OHLC } from "@/types"

interface OHLCChartProps {
  data: OHLC[]
  height?: number
}

export default function OHLCChart({ data, height = 400 }: OHLCChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return

    // Clear previous chart
    chartContainerRef.current.innerHTML = ""

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: "#333",
      },
      grid: {
        vertLines: { color: "#f0f0f0" },
        horzLines: { color: "#f0f0f0" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: "#d1d5db",
      },
      timeScale: {
        borderColor: "#d1d5db",
        timeVisible: true,
      },
      height,
    })

    chartRef.current = chart

    // Candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#ef4444",       // Red for up (Chinese convention)
      downColor: "#22c55e",     // Green for down
      borderUpColor: "#ef4444",
      borderDownColor: "#22c55e",
      wickUpColor: "#ef4444",
      wickDownColor: "#22c55e",
    })

    // Sort data by timestamp
    const sorted = [...data].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )

    candlestickSeries.setData(
      sorted.map((d) => ({
        time: (new Date(d.timestamp).getTime() / 1000) as any,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }))
    )

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: "#6b7280",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    })

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    })

    volumeSeries.setData(
      sorted.map((d) => ({
        time: (new Date(d.timestamp).getTime() / 1000) as any,
        value: d.volume,
        color: d.close >= d.open ? "rgba(239, 68, 68, 0.3)" : "rgba(34, 197, 94, 0.3)",
      }))
    )

    // Fit content
    chart.timeScale().fitContent()

    // Cleanup
    return () => {
      chart.remove()
    }
  }, [data, height])

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] text-muted-foreground">
        No data to display
      </div>
    )
  }

  return <div ref={chartContainerRef} />
}
