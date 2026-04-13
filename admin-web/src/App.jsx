import { Link, Route, Routes } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import LiveMapPage from './pages/LiveMapPage'
import AlertsPage from './pages/AlertsPage'
import AuditPage from './pages/AuditPage'

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <h2>لوحة الإدارة</h2>
        <Link to="/">الرئيسية</Link>
        <Link to="/live-map">المراقبة الحية</Link>
        <Link to="/alerts">التنبيهات</Link>
        <Link to="/audit">سجل التدقيق</Link>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/live-map" element={<LiveMapPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Routes>
      </main>
    </div>
  )
}
