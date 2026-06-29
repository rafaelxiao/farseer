import { Outlet, Link, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"

export default function Layout() {
  const location = useLocation()

  const navItems = [
    { path: "/", label: "Dashboard" },
    { path: "/ohlc", label: "OHLC" },
    { path: "/fundamentals", label: "Fundamentals" },
    { path: "/macro", label: "Macro" },
    { path: "/tasks", label: "Tasks" },
    { path: "/docs", label: "API Docs", external: true },
  ]

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
        <div className="max-w-6xl mx-auto flex h-14 items-center px-4">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-2xl font-bold tracking-tight">
              Farseer
            </Link>
            <nav className="flex items-center gap-1">
              {navItems.map((item) => (
                item.external ? (
                  <a
                    key={item.path}
                    href={`${import.meta.env.BASE_URL}docs`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1.5 rounded-md text-sm text-foreground/60 hover:text-foreground hover:bg-accent transition-colors"
                  >
                    {item.label}
                  </a>
                ) : (
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
                )
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-4">
        <Outlet />
      </main>
    </div>
  )
}
