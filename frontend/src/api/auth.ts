export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  is_admin: boolean
  is_approved: boolean
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  username: string
  is_admin: boolean
}

const TOKEN_KEY = "farseer-token"
const USER_KEY = "farseer-user"

// Get API base path from current URL
const getApiBase = () => {
  const base = import.meta.env.BASE_URL || "/"
  return `${base}api/v1`.replace(/\/+/g, "/")
}

const API_BASE = getApiBase()

export const authApi = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const formData = new URLSearchParams()
    formData.append("username", username)
    formData.append("password", password)

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "Login failed")
    }

    const data = await response.json()
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(data))
    return data
  },

  async register(username: string, email: string, password: string): Promise<void> {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "Registration failed")
    }
  },

  async getMe(): Promise<User> {
    const token = this.getToken()
    if (!token) throw new Error("Not authenticated")

    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!response.ok) {
      this.logout()
      throw new Error("Session expired")
    }

    return response.json()
  },

  async getUsers(): Promise<User[]> {
    const token = this.getToken()
    const response = await fetch(`${API_BASE}/auth/users`, {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!response.ok) {
      throw new Error("Failed to fetch users")
    }

    return response.json()
  },

  async approveUser(userId: number): Promise<void> {
    const token = this.getToken()
    const response = await fetch(`${API_BASE}/auth/users/${userId}/approve`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!response.ok) {
      throw new Error("Failed to approve user")
    }
  },

  async rejectUser(userId: number): Promise<void> {
    const token = this.getToken()
    const response = await fetch(`${API_BASE}/auth/users/${userId}/reject`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!response.ok) {
      throw new Error("Failed to reject user")
    }
  },

  async toggleUserActive(userId: number): Promise<void> {
    const token = this.getToken()
    const response = await fetch(`${API_BASE}/auth/users/${userId}/toggle-active`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!response.ok) {
      throw new Error("Failed to toggle user")
    }
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },

  getStoredUser(): LoginResponse | null {
    const stored = localStorage.getItem(USER_KEY)
    return stored ? JSON.parse(stored) : null
  },

  isAuthenticated(): boolean {
    return !!this.getToken()
  },

  isAdmin(): boolean {
    const user = this.getStoredUser()
    return user?.is_admin || false
  },

  logout(): void {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },
}
