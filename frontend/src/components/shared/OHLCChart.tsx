import { useEffect, useRef } from "react"
import { createChart, ColorType, CrosshairMode, CandlestickSeries, HistogramSeries, LineSeries } from "lightweight-charts"
import type { OHLC } from "@/types"
import type { ChartColors } from "./ChartSettings"

const MA_COLORS = ["#f59e0b", "#3b82f6", "#8b5cf6", "#ec4899", "#06b6d4"]

function calculateMA(closes: number[], period: number): (number | null)[] {
  const result: (number | null)[] = []
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = i - period + 1; j <= i; j++) sum += closes[j]
      result.push(sum / period)
    }
  }
  return result
}

interface OHLCChartProps {
  data: OHLC[]
  height?: number
  colors?: ChartColors
  logScale?: boolean
  maPeriods?: number[]
}

export default function OHLCChart({ data, height = 400, colors, logScale, maPeriods = [] }: OHLCChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<any>(null)
  const candleSeriesRef = useRef<any>(null)
  const volumeSeriesRef = useRef<any>(null)
  const maSeriesRefs = useRef<any[]>([])
  const prevDataLenRef = useRef(0)
  const isInitializedRef = useRef(false)
  
  // Price level lines
  // Create chart once
  useEffect(() => {
    if (!chartContainerRef.current) return

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
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: {
        borderColor: "#d1d5db",
        mode: logScale ? 1 : 0,
      },
      timeScale: { borderColor: "#d1d5db", timeVisible: true },
      height,
    })

    chartRef.current = chart

    const upColor = colors?.upColor || "#ef4444"
    const downColor = colors?.downColor || "#22c55e"

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor, downColor,
      borderUpColor: upColor, borderDownColor: downColor,
      wickUpColor: upColor, wickDownColor: downColor,
    })
    candleSeriesRef.current = candleSeries

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#6b7280",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    })
    chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } })
    volumeSeriesRef.current = volumeSeries

    maSeriesRefs.current = maPeriods.map((_, idx) => {
      return chart.addSeries(LineSeries, {
        color: MA_COLORS[idx % MA_COLORS.length],
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      })
    })

    return () => {
      chart.remove()
      chartRef.current = null
      candleSeriesRef.current = null
      volumeSeriesRef.current = null
      maSeriesRefs.current = []
      prevDataLenRef.current = 0
      isInitializedRef.current = false
    }
  }, [height])

  // Update log scale
  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.applyOptions({
        rightPriceScale: { mode: logScale ? 1 : 0 }
      })
    }
  }, [logScale])

  // Update data
  useEffect(() => {
    if (!chartRef.current || !candleSeriesRef.current || data.length === 0) return

    const sorted = [...data].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    const upColor = colors?.upColor || "#ef4444"
    const downColor = colors?.downColor || "#22c55e"

    candleSeriesRef.current.setData(
      sorted.map(d => ({
        time: (new Date(d.timestamp).getTime() / 1000) as any,
        open: d.open, high: d.high, low: d.low, close: d.close,
      }))
    )

    volumeSeriesRef.current.setData(
      sorted.map(d => ({
        time: (new Date(d.timestamp).getTime() / 1000) as any,
        value: d.volume,
        color: d.close >= d.open ? `${upColor}4D` : `${downColor}4D`,
      }))
    )

    const closes = sorted.map(d => d.close)
    const times = sorted.map(d => (new Date(d.timestamp).getTime() / 1000) as any)
    maPeriods.forEach((period, idx) => {
      if (maSeriesRefs.current[idx]) {
        const maData = calculateMA(closes, period)
        const lineData: any[] = []
        for (let i = 0; i < maData.length; i++) {
          if (maData[i] !== null) lineData.push({ time: times[i], value: maData[i] })
        }
        maSeriesRefs.current[idx].setData(lineData)
      }
    })

    const timeScale = chartRef.current.timeScale()
    
    if (!isInitializedRef.current) {
      timeScale.fitContent()
      isInitializedRef.current = true
      prevDataLenRef.current = data.length
    } else if (data.length > prevDataLenRef.current) {
      const visibleRange = timeScale.getVisibleLogicalRange()
      if (visibleRange) {
        const barsAdded = data.length - prevDataLenRef.current
        timeScale.setVisibleLogicalRange({
          from: visibleRange.from + barsAdded,
          to: visibleRange.to + barsAdded,
        })
      }
      prevDataLenRef.current = data.length
    }
  }, [data, colors, maPeriods])

  if (data.length === 0) {
    return <div className="flex items-center justify-center h-[400px] text-muted-foreground">No data to display</div>
  }

  return <div ref={chartContainerRef} />
}
