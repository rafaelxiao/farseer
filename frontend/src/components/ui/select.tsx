import { cn } from "@/lib/utils"

interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "size"> {
  options: SelectOption[]
  size?: "sm" | "md" | "lg"
}

const sizeClasses = {
  sm: "h-8 px-2 text-xs",
  md: "h-9 px-3 text-sm",
  lg: "h-10 px-4 text-base",
}

export function Select({ options, size = "md", className, ...props }: SelectProps) {
  return (
    <select
      className={cn(
        "rounded-md border border-input bg-background",
        "focus:outline-none focus:ring-2 focus:ring-ring",
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value} disabled={opt.disabled}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
