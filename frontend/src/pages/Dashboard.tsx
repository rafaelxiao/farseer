import { useQuery } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { tasksApi } from "@/api/tasks"

export default function Dashboard() {
  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => tasksApi.getJobs(),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card>
          <CardContent className="pt-4 pb-3">
            <div className="text-xs text-muted-foreground">Active Jobs</div>
            <div className="text-xl font-bold">{jobs?.length ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-3">
            <div className="text-xs text-muted-foreground">Last Status</div>
            <div className="text-xl font-bold">{jobs?.[0]?.last_status ?? "N/A"}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Quick Start</CardTitle>
        </CardHeader>
        <CardContent>
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
