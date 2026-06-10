import { cn } from "@/lib/utils"

interface DateInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> {
  label?: string
  size?: "sm" | "md" | "lg"
}

const sizeClasses = {
  sm: "h-8 px-2 text-xs",
  md: "h-9 px-3 text-sm",
  lg: "h-10 px-4 text-base",
}

export function DateInput({ label, size = "md", className, ...props }: DateInputProps) {
  return (
    <div className="flex items-center gap-1.5">
      {label && (
        <label className="text-xs text-muted-foreground whitespace-nowrap">
          {label}
        </label>
      )}
      <input
        type="date"
        className={cn(
          "rounded-md border border-input bg-background",
          "focus:outline-none focus:ring-2 focus:ring-ring",
          sizeClasses[size],
          className
        )}
        {...props}
      />
    </div>
  )
}
