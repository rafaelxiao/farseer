import { useState, useRef, useEffect } from "react"

interface DatePickerProps {
  value: string
  onChange: (value: string) => void
  label?: string
}

export default function DatePicker({ value, onChange, label }: DatePickerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [viewMode, setViewMode] = useState<"days" | "months" | "years">("days")
  const [currentDate, setCurrentDate] = useState(() => {
    if (value) {
      const d = new Date(value)
      return new Date(d.getFullYear(), d.getMonth(), 1)
    }
    return new Date(new Date().getFullYear(), new Date().getMonth(), 1)
  })
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedDate = value ? new Date(value + "T00:00:00") : null

  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  const DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
        setViewMode("days")
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const getDaysInMonth = (y: number, m: number) => new Date(y, m + 1, 0).getDate()
  const getFirstDayOfMonth = (y: number, m: number) => new Date(y, m, 1).getDay()

  const handlePrev = () => {
    if (viewMode === "years") {
      setCurrentDate(new Date(year - 12, month, 1))
    } else if (viewMode === "months") {
      setCurrentDate(new Date(year - 1, month, 1))
    } else {
      setCurrentDate(new Date(year, month - 1, 1))
    }
  }

  const handleNext = () => {
    if (viewMode === "years") {
      setCurrentDate(new Date(year + 12, month, 1))
    } else if (viewMode === "months") {
      setCurrentDate(new Date(year + 1, month, 1))
    } else {
      setCurrentDate(new Date(year, month + 1, 1))
    }
  }

  const handleSelectDay = (day: number) => {
    const selected = new Date(year, month, day)
    const dateStr = selected.toISOString().split("T")[0]
    onChange(dateStr)
    setIsOpen(false)
    setViewMode("days")
  }

  const handleSelectMonth = (m: number) => {
    setCurrentDate(new Date(year, m, 1))
    setViewMode("days")
  }

  const handleSelectYear = (y: number) => {
    setCurrentDate(new Date(y, month, 1))
    setViewMode("months")
  }

  const renderDays = () => {
    const daysInMonth = getDaysInMonth(year, month)
    const firstDay = getFirstDayOfMonth(year, month)
    const days = []

    // Empty cells for days before first day
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-8 w-8" />)
    }

    // Day cells
    for (let d = 1; d <= daysInMonth; d++) {
      const isSelected = selectedDate && 
        selectedDate.getFullYear() === year && 
        selectedDate.getMonth() === month && 
        selectedDate.getDate() === d
      const isToday = new Date().toISOString().split("T")[0] === `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`

      days.push(
        <button
          key={d}
          onClick={() => handleSelectDay(d)}
          className={`h-8 w-8 rounded-md text-sm flex items-center justify-center transition-colors
            ${isSelected ? "bg-primary text-primary-foreground font-bold" : ""}
            ${isToday && !isSelected ? "border border-primary" : ""}
            ${!isSelected ? "hover:bg-accent" : ""}
          `}
        >
          {d}
        </button>
      )
    }

    return (
      <div>
        <div className="grid grid-cols-7 gap-1 mb-1">
          {DAYS.map((d) => (
            <div key={d} className="h-8 w-8 text-xs text-muted-foreground flex items-center justify-center font-medium">
              {d}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {days}
        </div>
      </div>
    )
  }

  const renderMonths = () => {
    return (
      <div className="grid grid-cols-3 gap-2">
        {MONTHS.map((m, i) => {
          const isSelected = selectedDate && selectedDate.getFullYear() === year && selectedDate.getMonth() === i
          return (
            <button
              key={m}
              onClick={() => handleSelectMonth(i)}
              className={`h-10 rounded-md text-sm transition-colors
                ${isSelected ? "bg-primary text-primary-foreground font-bold" : "hover:bg-accent"}
              `}
            >
              {m}
            </button>
          )
        })}
      </div>
    )
  }

  const renderYears = () => {
    const startYear = Math.floor(year / 12) * 12
    const years = []
    for (let y = startYear - 1; y <= startYear + 12; y++) {
      years.push(y)
    }

    return (
      <div className="grid grid-cols-4 gap-2">
        {years.map((y) => {
          const isSelected = selectedDate && selectedDate.getFullYear() === y
          const isOutside = y < startYear || y >= startYear + 12
          return (
            <button
              key={y}
              onClick={() => handleSelectYear(y)}
              className={`h-10 rounded-md text-sm transition-colors
                ${isSelected ? "bg-primary text-primary-foreground font-bold" : ""}
                ${isOutside ? "text-muted-foreground" : ""}
                ${!isSelected ? "hover:bg-accent" : ""}
              `}
            >
              {y}
            </button>
          )
        })}
      </div>
    )
  }

  const getHeaderLabel = () => {
    if (viewMode === "years") {
      const startYear = Math.floor(year / 12) * 12
      return `${startYear} - ${startYear + 11}`
    }
    if (viewMode === "months") {
      return `${year}`
    }
    return `${MONTHS[month]} ${year}`
  }

  const displayValue = value ? new Date(value + "T00:00:00").toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" }) : ""

  return (
    <div ref={containerRef} className="relative inline-block">
      {label && <label className="text-xs text-muted-foreground mr-1">{label}</label>}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="h-8 rounded border border-input bg-background px-2 text-sm text-left min-w-[120px] hover:bg-accent transition-colors"
      >
        {displayValue || "Select date"}
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 bg-background border rounded-lg shadow-lg p-3 w-[280px]">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <button onClick={handlePrev} className="h-7 w-7 rounded hover:bg-accent flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6" />
              </svg>
            </button>
            <button
              onClick={() => {
                if (viewMode === "days") setViewMode("months")
                else if (viewMode === "months") setViewMode("years")
              }}
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              {getHeaderLabel()}
            </button>
            <button onClick={handleNext} className="h-7 w-7 rounded hover:bg-accent flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>

          {/* Content */}
          {viewMode === "days" && renderDays()}
          {viewMode === "months" && renderMonths()}
          {viewMode === "years" && renderYears()}

          {/* Today button */}
          <div className="mt-3 pt-2 border-t">
            <button
              onClick={() => {
                const today = new Date().toISOString().split("T")[0]
                onChange(today)
                setIsOpen(false)
                setViewMode("days")
              }}
              className="w-full text-sm text-primary hover:bg-accent rounded py-1 transition-colors"
            >
              Today
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
