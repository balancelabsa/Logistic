import { useEffect, useState } from 'react'
import api from '../api/client'

export default function DashboardPage() {
  const [data, setData] = useState({})
  useEffect(() => {
    api.get('/admin/reports/overview').then((res) => setData(res.data)).catch(() => {})
  }, [])

  return (
    <section>
      <h1>لوحة المؤشرات</h1>
      <div className="grid">
        <div className="card">إجمالي السائقين: {data.drivers}</div>
        <div className="card">السائقون النشطون: {data.active_drivers}</div>
        <div className="card">الورديات النشطة: {data.active_shifts}</div>
        <div className="card">الزيارات المتأخرة: {data.delayed_visits}</div>
        <div className="card">الزيارات الفائتة: {data.missed_visits}</div>
        <div className="card">التنبيهات المفتوحة: {data.open_alerts}</div>
        <div className="card">التوقفات الطويلة: {data.long_stops}</div>
      </div>
    </section>
  )
}
