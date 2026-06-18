import { useState, useRef, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { ohlcApi } from "@/api/ohlc"

interface SymbolSearchProps {
  value: string
  onSelect: (symbol: string) => void
  assetType?: "stock" | "etf"
}

function isETFCode(symbol: string): boolean {
  const code = symbol.split(".")[0]
  return (
    (code.startsWith("51") || code.startsWith("58") || code.startsWith("15")) &&
    code.length === 6
  )
}

export default function SymbolSearch({ value, onSelect, assetType }: SymbolSearchProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const { data: symbols } = useQuery({
    queryKey: ["symbols"],
    queryFn: () => ohlcApi.listSymbols(),
    staleTime: 5 * 60 * 1000,
  })

  // Filter symbols based on search and asset type
  const filtered = symbols?.filter((s) => {
    const q = search.toLowerCase()
    const matchesSearch = s.symbol.toLowerCase().includes(q)
    const matchesType = assetType
      ? assetType === "etf"
        ? isETFCode(s.symbol)
        : !isETFCode(s.symbol)
      : true
    return matchesSearch && matchesType
  }) || []

  const displayed = filtered.slice(0, 50)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleSelect = (symbol: string) => {
    onSelect(symbol)
    setSearch("")
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={isOpen ? search : value}
        onChange={(e) => {
          setSearch(e.target.value)
          if (!isOpen) setIsOpen(true)
        }}
        onFocus={() => {
          setIsOpen(true)
          setSearch("")
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" && displayed.length === 1) {
            handleSelect(displayed[0].symbol)
          }
          if (e.key === "Escape") {
            setIsOpen(false)
            setSearch("")
          }
        }}
        className="h-8 w-36 rounded border border-input bg-background px-2 text-sm"
        placeholder={assetType === "etf" ? "Search ETF..." : "Search symbol..."}
      />

      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute z-50 mt-1 max-h-80 w-64 overflow-auto rounded-md border bg-white shadow-md"
        >
          {displayed.length === 0 ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              No symbols found
            </div>
          ) : (
            <div className="py-1">
              {displayed.map((s) => (
                <button
                  key={s.symbol}
                  className="flex w-full items-center justify-between px-3 py-1.5 text-sm hover:bg-accent"
                  onClick={() => handleSelect(s.symbol)}
                >
                  <span className="font-medium">{s.symbol}</span>
                  <span className="text-xs text-muted-foreground">
                    {s.records.toLocaleString()} bars
                  </span>
                </button>
              ))}
              {filtered.length > 50 && (
                <div className="px-3 py-1.5 text-xs text-muted-foreground">
                  Showing 50 of {filtered.length} results
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
