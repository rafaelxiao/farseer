import { useState } from "react"
import DatePicker from "./DatePicker"

interface PlaybackStartDialogProps {
  isOpen: boolean
  onClose: () => void
  onStart: (startDate: string) => void
  minDate?: string
  maxDate?: string
  symbol: string
}

export default function PlaybackStartDialog({
  isOpen,
  onClose,
  onStart,
  minDate,
  maxDate,
  symbol,
}: PlaybackStartDialogProps) {
  const [startDate, setStartDate] = useState(() => {
    // Default to 1 year ago
    const d = new Date()
    d.setFullYear(d.getFullYear() - 1)
    return d.toISOString().split("T")[0]
  })
  const [error, setError] = useState("")

  if (!isOpen) return null

  const handleStart = () => {
    setError("")

    if (maxDate && startDate > maxDate) {
      setError(`Date must be before ${maxDate}`)
      return
    }

    onStart(startDate)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Dialog */}
      <div className="relative bg-background border rounded-lg shadow-xl p-6 w-[360px]">
        <h2 className="text-lg font-bold mb-1">Start Playback</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Select the starting date for {symbol}
        </p>

        {error && (
          <div className="mb-3 p-2 text-sm text-red-600 bg-red-50 rounded">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium block mb-2">Start From</label>
            <DatePicker
              value={startDate}
              onChange={setStartDate}
            />
            {minDate && (
              <p className="text-xs text-muted-foreground mt-1">
                Data range: {minDate} to {maxDate || "present"}
              </p>
            )}
          </div>

          {/* Quick presets */}
          <div>
            <label className="text-sm font-medium block mb-2">Quick Select</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "1 Month Ago", months: 1 },
                { label: "3 Months Ago", months: 3 },
                { label: "6 Months Ago", months: 6 },
                { label: "1 Year Ago", months: 12 },
                { label: "2 Years Ago", months: 24 },
                { label: "From IPO", months: -1 },
              ].map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => {
                    if (preset.months === -1) {
                      // IPO date - use 1990-12-19 (Shanghai exchange start)
                      setStartDate("1990-12-19")
                    } else {
                      const d = new Date()
                      d.setMonth(d.getMonth() - preset.months)
                      setStartDate(d.toISOString().split("T")[0])
                    }
                  }}
                  className="px-3 py-2 text-sm border rounded hover:bg-accent transition-colors"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded hover:bg-accent transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleStart}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
          >
            Start Playback
          </button>
        </div>
      </div>
    </div>
  )
}
