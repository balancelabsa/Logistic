import { useEffect, useState } from 'react'
import axios from 'axios'
import StatCard from '../components/StatCard'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000' })

export default function DashboardPage() {
  const [data, setData] = useState({})

  useEffect(() => {
    api.get('/admin/reports/overview').then((res) => setData(res.data)).catch(() => {})
  }, [])

  return (
    <section>
      <h1>ملخص التشغيل</h1>
      <div className="grid">
        <StatCard title="عدد السائقين" value={data.drivers} />
        <StatCard title="الورديات النشطة" value={data.active_shifts} />
        <StatCard title="الزيارات المنفذة" value={data.visits_done} />
        <StatCard title="إجمالي التنبيهات" value={data.total_alerts} />
      </div>
    </section>
  )
}
