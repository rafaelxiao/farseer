import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { tasksApi } from "@/api/tasks"

export default function Tasks() {
  const queryClient = useQueryClient()

  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => tasksApi.getJobs(),
  })

  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ["task-runs"],
    queryFn: () => tasksApi.getRuns({ limit: 20 }),
  })

  const triggerMutation = useMutation({
    mutationFn: (jobId: string) => tasksApi.trigger(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["task-runs"] })
      queryClient.invalidateQueries({ queryKey: ["jobs"] })
    },
  })

  const statusVariant = (status: string) => {
    switch (status) {
      case "success": return "success"
      case "failed": return "destructive"
      case "running": return "warning"
      default: return "secondary"
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Tasks</h1>

      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-base">Scheduled Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {jobsLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : jobs && jobs.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs">Job ID</TableHead>
                    <TableHead className="text-xs">Status</TableHead>
                    <TableHead className="text-xs">Last Run</TableHead>
                    <TableHead className="text-xs">Next Run</TableHead>
                    <TableHead className="text-xs text-right">Runs</TableHead>
                    <TableHead className="text-xs text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.job_id}>
                      <TableCell className="text-sm font-medium">{job.job_id}</TableCell>
                      <TableCell>
                        <Badge variant={statusVariant(job.last_status ?? "")} className="text-xs">
                          {job.last_status ?? "never"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs">
                        {job.last_run ? new Date(job.last_run).toLocaleString() : "-"}
                      </TableCell>
                      <TableCell className="text-xs">
                        {job.next_run ? new Date(job.next_run).toLocaleString() : "-"}
                      </TableCell>
                      <TableCell className="text-sm text-right">{job.total_runs}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => triggerMutation.mutate(job.job_id)}
                          disabled={triggerMutation.isPending}
                        >
                          Run
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No jobs registered</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-base">Recent Runs</CardTitle>
        </CardHeader>
        <CardContent>
          {runsLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : runs && runs.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs">Job ID</TableHead>
                    <TableHead className="text-xs">Status</TableHead>
                    <TableHead className="text-xs">Started</TableHead>
                    <TableHead className="text-xs">Finished</TableHead>
                    <TableHead className="text-xs">Result</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => (
                    <TableRow key={run.id}>
                      <TableCell className="text-sm font-medium">{run.job_id}</TableCell>
                      <TableCell>
                        <Badge variant={statusVariant(run.status)} className="text-xs">
                          {run.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs">
                        {run.started_at ? new Date(run.started_at).toLocaleString() : "-"}
                      </TableCell>
                      <TableCell className="text-xs">
                        {run.finished_at ? new Date(run.finished_at).toLocaleString() : "-"}
                      </TableCell>
                      <TableCell className="text-xs max-w-xs truncate">{run.result ?? "-"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No runs yet</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
