// API base path - adjust based on environment
const getApiBase = () => {
  // If served under /farseer/dev/, use that prefix for API calls
  const base = import.meta.env.BASE_URL || "/"
  return `${base}api/v1`.replace(/\/+/g, "/")
}

const API_BASE = getApiBase()

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  })

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }

  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
}
