import { Routes, Route } from "react-router-dom"
import Layout from "@/components/layout/Layout"
import Dashboard from "@/pages/Dashboard"
import OHLCViewer from "@/pages/OHLCViewer"
import FundamentalsViewer from "@/pages/FundamentalsViewer"
import Tasks from "@/pages/Tasks"
import Login from "@/pages/Login"
import Register from "@/pages/Register"
import AdminUsers from "@/pages/AdminUsers"
import MyPerformance from "@/pages/MyPerformance"

export default function App() {
  return (
    <Routes>
      {/* Public routes (no auth required) */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected routes (auth required) */}
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="ohlc" element={<OHLCViewer />} />
        <Route path="fundamentals" element={<FundamentalsViewer />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="performance" element={<MyPerformance />} />
        <Route path="admin/users" element={<AdminUsers />} />
      </Route>
    </Routes>
  )
}
