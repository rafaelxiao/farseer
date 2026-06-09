import { api } from "./client"
import type { TaskRun, TaskJob } from "@/types"

export const tasksApi = {
  getRuns: (params?: { job_id?: string; status?: string; limit?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.job_id) searchParams.set("job_id", params.job_id)
    if (params?.status) searchParams.set("status", params.status)
    if (params?.limit) searchParams.set("limit", String(params.limit))
    return api.get<TaskRun[]>(`/tasks/?${searchParams}`)
  },

  getJobs: () => api.get<TaskJob[]>("/tasks/jobs"),

  trigger: (jobId: string) => api.post(`/tasks/trigger/${jobId}`, {}),
}
