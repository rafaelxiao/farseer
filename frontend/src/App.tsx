import { Routes, Route } from "react-router-dom"
import Layout from "@/components/layout/Layout"
import Dashboard from "@/pages/Dashboard"
import OHLCViewer from "@/pages/OHLCViewer"
import FundamentalsViewer from "@/pages/FundamentalsViewer"
import MacroViewer from "@/pages/MacroViewer"
import Tasks from "@/pages/Tasks"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="ohlc" element={<OHLCViewer />} />
        <Route path="fundamentals" element={<FundamentalsViewer />} />
        <Route path="macro" element={<MacroViewer />} />
        <Route path="tasks" element={<Tasks />} />
      </Route>
    </Routes>
  )
}
