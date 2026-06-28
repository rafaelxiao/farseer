// API base path - adjust based on environment
const getApiBase = () => {
  // If served under /farseer/dev/, use that prefix for API calls
  const base = import.meta.env.BASE_URL || "/"
  return `${base}api/v1`.replace(/\/+/g, "/")
}

const API_BASE = getApiBase()

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  
  const apiKey = import.meta.env.VITE_API_KEY
  if (apiKey) {
    headers["X-API-Key"] = apiKey
  }
  
  const res = await fetch(url, {
    headers: { ...headers, ...options?.headers },
    ...options,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `API error: ${res.status}`)
  }

  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
}
