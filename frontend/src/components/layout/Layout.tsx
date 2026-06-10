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
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
        <div className="container flex h-10 items-center px-4">
          <Link to="/" className="mr-4 font-bold text-sm">
            Farseer
          </Link>
          <nav className="flex items-center gap-3 text-sm">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "transition-colors hover:text-foreground/80",
                  location.pathname === item.path
                    ? "text-foreground font-medium"
                    : "text-foreground/60"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="container px-4 py-4">
        <Outlet />
      </main>
    </div>
  )
}
