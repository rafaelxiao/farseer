import { Outlet, Link, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"

const navItems = [
  { path: "/", label: "Dashboard" },
  { path: "/ohlc", label: "OHLC" },
  { path: "/fundamentals", label: "Fundamentals" },
  { path: "/tasks", label: "Tasks" },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
        <div className="max-w-6xl mx-auto flex h-12 items-center justify-between px-4">
          <Link to="/" className="text-lg font-bold tracking-tight">
            Farseer
          </Link>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "px-3 py-1.5 rounded-md text-sm transition-colors",
                  location.pathname === item.path
                    ? "bg-primary text-primary-foreground font-medium"
                    : "text-foreground/60 hover:text-foreground hover:bg-accent"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-4">
        <Outlet />
      </main>
    </div>
  )
}
