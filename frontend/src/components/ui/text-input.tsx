import { cn } from "@/lib/utils"

interface TextInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> {
  size?: "sm" | "md" | "lg"
}

const sizeClasses = {
  sm: "h-8 px-2 text-xs",
  md: "h-9 px-3 text-sm",
  lg: "h-10 px-4 text-base",
}

export function TextInput({ size = "md", className, ...props }: TextInputProps) {
  return (
    <input
      type="text"
      className={cn(
        "rounded-md border border-input bg-background",
        "focus:outline-none focus:ring-2 focus:ring-ring",
        "placeholder:text-muted-foreground",
        sizeClasses[size],
        className
      )}
      {...props}
    />
  )
}
