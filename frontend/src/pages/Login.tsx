import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { authApi } from "@/api/auth"

export default function Login() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      await authApi.login(username, password)
      navigate("/")
      window.location.reload()
    } catch (err: any) {
      setError(err.message || "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Farseer Login</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Enter username"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Enter password"
                required
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </Button>

            <div className="text-center text-sm text-muted-foreground">
              Don't have an account?{" "}
              <a href="/farseer/dev/register" className="text-primary hover:underline">
                Register
              </a>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
