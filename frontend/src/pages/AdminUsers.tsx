import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { authApi, type User } from "@/api/auth"

export default function AdminUsers() {
  const queryClient = useQueryClient()

  const { data: users, isLoading } = useQuery<User[]>({
    queryKey: ["users"],
    queryFn: () => authApi.getUsers(),
  })

  const approveMutation = useMutation({
    mutationFn: (userId: number) => authApi.approveUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  })

  const rejectMutation = useMutation({
    mutationFn: (userId: number) => authApi.rejectUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  })

  const toggleActiveMutation = useMutation({
    mutationFn: (userId: number) => authApi.toggleUserActive(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  })

  const pendingUsers = users?.filter((u) => !u.is_approved && u.is_active) || []
  const rejectedUsers = users?.filter((u) => !u.is_approved && !u.is_active) || []
  const approvedUsers = users?.filter((u) => u.is_approved) || []

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">User Management</h1>
        <p className="text-sm text-muted-foreground">Manage user registrations and access</p>
      </div>

      {/* Pending Approvals */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            Pending Approvals
            {pendingUsers.length > 0 && (
              <Badge variant="destructive">{pendingUsers.length}</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : pendingUsers.length === 0 ? (
            <p className="text-sm text-muted-foreground">No pending registrations</p>
          ) : (
            <div className="space-y-3">
              {pendingUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <div className="font-medium">{user.username}</div>
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                    <div className="text-xs text-muted-foreground">
                      Registered: {new Date(user.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => approveMutation.mutate(user.id)}
                      disabled={approveMutation.isPending}
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => rejectMutation.mutate(user.id)}
                      disabled={rejectMutation.isPending}
                    >
                      Reject
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Rejected Users */}
      {rejectedUsers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              Rejected Users
              <Badge variant="secondary">{rejectedUsers.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {rejectedUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-3 border rounded-lg bg-muted/50"
                >
                  <div>
                    <div className="font-medium">{user.username}</div>
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => approveMutation.mutate(user.id)}
                    disabled={approveMutation.isPending}
                  >
                    Approve
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Users */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">All Users</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : approvedUsers.length === 0 ? (
            <p className="text-sm text-muted-foreground">No approved users</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-3">Username</th>
                    <th className="text-left py-2 px-3">Email</th>
                    <th className="text-left py-2 px-3">Role</th>
                    <th className="text-left py-2 px-3">Status</th>
                    <th className="text-left py-2 px-3">Joined</th>
                    <th className="text-right py-2 px-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {approvedUsers.map((user) => (
                    <tr key={user.id} className="border-b">
                      <td className="py-2 px-3 font-medium">{user.username}</td>
                      <td className="py-2 px-3 text-muted-foreground">{user.email}</td>
                      <td className="py-2 px-3">
                        {user.is_admin ? (
                          <Badge variant="default">Admin</Badge>
                        ) : (
                          <Badge variant="outline">User</Badge>
                        )}
                      </td>
                      <td className="py-2 px-3">
                        {user.is_active ? (
                          <Badge variant="success" className="bg-green-100 text-green-800">Active</Badge>
                        ) : (
                          <Badge variant="secondary">Inactive</Badge>
                        )}
                      </td>
                      <td className="py-2 px-3 text-muted-foreground">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-2 px-3 text-right">
                        {!user.is_admin && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => toggleActiveMutation.mutate(user.id)}
                            disabled={toggleActiveMutation.isPending}
                          >
                            {user.is_active ? "Deactivate" : "Activate"}
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
