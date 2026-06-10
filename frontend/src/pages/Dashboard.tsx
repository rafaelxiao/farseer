import { Card, CardContent } from "@/components/ui/card"

export default function Dashboard() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card>
          <CardContent className="py-3">
            <div className="text-xs text-muted-foreground">Symbols</div>
            <div className="text-xl font-bold">—</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-3">
            <div className="text-xs text-muted-foreground">Records</div>
            <div className="text-xl font-bold">—</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="py-3">
          <div className="text-sm text-muted-foreground space-y-1">
            <p>• <strong>OHLC</strong> — View price data with charts</p>
            <p>• <strong>Fundamentals</strong> — Financial data</p>
            <p>• <strong>Tasks</strong> — Manage data fetchers</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
