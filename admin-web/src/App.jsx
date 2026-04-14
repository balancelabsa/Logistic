import { Link, Route, Routes } from 'react-router-dom'
import { useEffect, useState } from 'react'
import RequireAuth from './components/RequireAuth'
import { useAuth } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import LiveMapPage from './pages/LiveMapPage'
import AlertsPage from './pages/AlertsPage'
import AuditPage from './pages/AuditPage'
import ReportsPage from './pages/ReportsPage'
import VisitsComparisonPage from './pages/VisitsComparisonPage'
import RouteHistoryPage from './pages/RouteHistoryPage'
import api from './api/client'

function Shell() {
  const { logout, user } = useAuth()
  const [count, setCount] = useState(0)
  const [lastId, setLastId] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      api.get('/admin/notifications', { params: { since_id: lastId } }).then((res) => {
        if (res.data.items.length) {
          setCount((v) => v + res.data.items.length)
          setLastId(res.data.items[res.data.items.length - 1].id)
        }
      }).catch(() => {})
    }, 8000)
    return () => clearInterval(timer)
  }, [lastId])

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2>لوحة الإدارة</h2>
        <p>{user?.full_name}</p>
        <p>الإشعارات: {count}</p>
        <Link to="/">الرئيسية</Link>
        <Link to="/live-map">المراقبة الحية</Link>
        <Link to="/route-history">مسار السائقين</Link>
        <Link to="/visits">المخطط مقابل الفعلي</Link>
        <Link to="/alerts">التنبيهات</Link>
        <Link to="/audit">التدقيق</Link>
        <Link to="/reports">التقارير</Link>
        <button onClick={logout}>تسجيل الخروج</button>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/live-map" element={<LiveMapPage />} />
          <Route path="/route-history" element={<RouteHistoryPage />} />
          <Route path="/visits" element={<VisitsComparisonPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/reports" element={<ReportsPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={<RequireAuth><Shell /></RequireAuth>} />
    </Routes>
  )
}
