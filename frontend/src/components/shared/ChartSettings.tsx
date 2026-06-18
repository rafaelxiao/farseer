export interface ChartColors {
  upColor: string
  downColor: string
}

const DEFAULT_COLORS: ChartColors = {
  upColor: "#ef4444",   // red
  downColor: "#22c55e", // green
}

const STORAGE_KEY = "farseer-chart-colors"

export function getChartColors(): ChartColors {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return { ...DEFAULT_COLORS, ...JSON.parse(saved) }
    }
  } catch {}
  return DEFAULT_COLORS
}

export function resetChartColors() {
  localStorage.removeItem(STORAGE_KEY)
  return DEFAULT_COLORS
}

interface ChartSettingsProps {
  colors: ChartColors
  onChange: (colors: ChartColors) => void
  onReset: () => void
}

export default function ChartSettings({ colors, onChange, onReset }: ChartSettingsProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5">
        <label className="text-xs text-muted-foreground">Up</label>
        <input
          type="color"
          value={colors.upColor}
          onChange={(e) => onChange({ ...colors, upColor: e.target.value })}
          className="h-6 w-6 cursor-pointer rounded border"
        />
      </div>
      <div className="flex items-center gap-1.5">
        <label className="text-xs text-muted-foreground">Down</label>
        <input
          type="color"
          value={colors.downColor}
          onChange={(e) => onChange({ ...colors, downColor: e.target.value })}
          className="h-6 w-6 cursor-pointer rounded border"
        />
      </div>
      <button
        onClick={onReset}
        className="text-xs text-muted-foreground hover:text-foreground underline"
      >
        Reset
      </button>
    </div>
  )
}
