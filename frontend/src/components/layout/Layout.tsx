import { useState, useRef, useEffect } from "react"
import { Outlet, Link, useLocation, useNavigate, Navigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { authApi } from "@/api/auth"

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const isAuthenticated = authApi.isAuthenticated()
  const isAdmin = authApi.isAdmin()
  const user = authApi.getStoredUser()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // Public routes that don't require auth
  const publicRoutes = ["/login", "/register"]
  const isPublicRoute = publicRoutes.includes(location.pathname)

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  // Close menu on route change
  useEffect(() => {
    setShowUserMenu(false)
  }, [location.pathname])

  // Redirect to login if not authenticated and not on a public route
  if (!isAuthenticated && !isPublicRoute) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  const navItems = [
    { path: "/", label: "Dashboard" },
    { path: "/ohlc", label: "OHLC" },
    { path: "/fundamentals", label: "Fundamentals" },
    { path: "/tasks", label: "Tasks" },
    { path: "/docs", label: "API Docs", external: true },
  ]

  const handleLogout = () => {
    authApi.logout()
    navigate("/login")
    window.location.reload()
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
        <div className="max-w-6xl mx-auto flex h-14 items-center justify-between px-4">
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

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm hover:bg-accent transition-colors"
                >
                  <span className="font-medium">{user?.username}</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-1 w-48 bg-background border rounded-md shadow-lg py-1 z-50">
                    <Link
                      to="/performance"
                      className="block px-4 py-2 text-sm hover:bg-accent transition-colors"
                    >
                      My Performance
                    </Link>
                    {isAdmin && (
                      <Link
                        to="/admin/users"
                        className="block px-4 py-2 text-sm hover:bg-accent transition-colors"
                      >
                        User Management
                      </Link>
                    )}
                    <div className="border-t my-1" />
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm hover:bg-accent transition-colors text-red-600"
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-3 py-1.5 rounded-md text-sm text-foreground/60 hover:text-foreground hover:bg-accent transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-1.5 rounded-md text-sm bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-4">
        <Outlet />
      </main>
    </div>
  )
}
