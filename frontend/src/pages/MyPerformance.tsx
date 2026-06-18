import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api } from "@/api/client"
import { authApi } from "@/api/auth"

interface SavedGame {
  id: number
  symbol: string
  timeframe: string
  start_date: string
  end_date: string
  initial_capital: number
  status: string
  created_at: string
  stats?: GameStats
}

interface GameStats {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  total_return: number
  total_return_pct: number
  max_drawdown: number
  max_drawdown_pct: number
  avg_holding_bars: number
  profit_factor: number
  sharpe_ratio: number
  final_capital: number
  peak_capital: number
}

export default function MyPerformance() {
  const queryClient = useQueryClient()
  const isAuthenticated = authApi.isAuthenticated()

  const { data: games, isLoading } = useQuery<SavedGame[]>({
    queryKey: ["my-games"],
    queryFn: () => api.get("/game/my-games"),
    enabled: isAuthenticated,
  })

  // Load stats for each game
  const gamesWithStats = useQuery({
    queryKey: ["my-games-stats", games?.map(g => g.id)],
    queryFn: async () => {
      if (!games) return []
      const results = await Promise.all(
        games.map(async (game) => {
          try {
            const stats = await api.get(`/game/${game.id}/stats`)
            return { ...game, stats }
          } catch {
            return game
          }
        })
      )
      return results
    },
    enabled: !!games && games.length > 0,
  })

  const data = gamesWithStats.data || games || []

  // Calculate aggregate stats
  const completedGames = data.filter(g => g.stats && g.status === "completed")
  const totalGames = data.length
  const avgWinRate = completedGames.length > 0
    ? completedGames.reduce((sum, g) => sum + (g.stats?.win_rate || 0), 0) / completedGames.length
    : 0
  const avgReturn = completedGames.length > 0
    ? completedGames.reduce((sum, g) => sum + (g.stats?.total_return_pct || 0), 0) / completedGames.length
    : 0
  const bestGame = completedGames.reduce((best, g) =>
    (g.stats?.total_return_pct || 0) > (best?.stats?.total_return_pct || 0) ? g : best, completedGames[0])
  const worstGame = completedGames.reduce((worst, g) =>
    (g.stats?.total_return_pct || 0) < (worst?.stats?.total_return_pct || 0) ? g : worst, completedGames[0])

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-[400px]">
        <div className="text-center">
          <p className="text-lg font-medium">Please login to view performance</p>
          <a href="/farseer/dev/login" className="text-primary hover:underline mt-2 inline-block">Login</a>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My Performance</h1>
        <p className="text-sm text-muted-foreground">Track your trading game results</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="py-4">
            <div className="text-xs text-muted-foreground">Total Games</div>
            <div className="text-2xl font-bold">{totalGames}</div>
            <div className="text-xs text-muted-foreground">{completedGames.length} completed</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="text-xs text-muted-foreground">Avg Win Rate</div>
            <div className="text-2xl font-bold">{avgWinRate.toFixed(1)}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="text-xs text-muted-foreground">Avg Return</div>
            <div className={`text-2xl font-bold ${avgReturn >= 0 ? "text-green-600" : "text-red-600"}`}>
              {avgReturn >= 0 ? "+" : ""}{avgReturn.toFixed(2)}%
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="text-xs text-muted-foreground">Best / Worst</div>
            <div className="text-sm">
              <span className="text-green-600">+{bestGame?.stats?.total_return_pct?.toFixed(2) || 0}%</span>
              {" / "}
              <span className="text-red-600">{worstGame?.stats?.total_return_pct?.toFixed(2) || 0}%</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Games List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Game History</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No games played yet. Start a playback to begin!</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-3">Symbol</th>
                    <th className="text-left py-2 px-3">Date</th>
                    <th className="text-right py-2 px-3">Trades</th>
                    <th className="text-right py-2 px-3">Win Rate</th>
                    <th className="text-right py-2 px-3">Return</th>
                    <th className="text-right py-2 px-3">Max DD</th>
                    <th className="text-right py-2 px-3">Sharpe</th>
                    <th className="text-left py-2 px-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((game) => (
                    <tr key={game.id} className="border-b hover:bg-accent/50">
                      <td className="py-2 px-3 font-medium">{game.symbol}</td>
                      <td className="py-2 px-3 text-muted-foreground">
                        {new Date(game.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-2 px-3 text-right">{game.stats?.total_trades || 0}</td>
                      <td className="py-2 px-3 text-right">{game.stats?.win_rate?.toFixed(1) || 0}%</td>
                      <td className={`py-2 px-3 text-right font-medium ${(game.stats?.total_return_pct || 0) >= 0 ? "text-green-600" : "text-red-600"}`}>
                        {(game.stats?.total_return_pct || 0) >= 0 ? "+" : ""}{game.stats?.total_return_pct?.toFixed(2) || 0}%
                      </td>
                      <td className="py-2 px-3 text-right text-red-600">
                        -{game.stats?.max_drawdown_pct?.toFixed(2) || 0}%
                      </td>
                      <td className="py-2 px-3 text-right">{game.stats?.sharpe_ratio?.toFixed(2) || 0}</td>
                      <td className="py-2 px-3">
                        <Badge variant={game.status === "completed" ? "default" : game.status === "active" ? "success" : "secondary"}>
                          {game.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Performance Chart Placeholder */}
      {completedGames.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Performance Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
              Performance chart coming soon...
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
