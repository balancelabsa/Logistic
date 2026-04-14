import { useState } from 'react'

export default function ReportsPage() {
  const [driverId, setDriverId] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const base = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  return (
    <section>
      <h1>التقارير</h1>
      <p>تقرير PDF قابل للطباعة.</p>
      <input placeholder="driver_id" value={driverId} onChange={(e) => setDriverId(e.target.value)} />
      <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      <a href={`${base}/admin/reports/route-pdf?driver_id=${driverId}&date=${date}`} target="_blank">تصدير PDF</a>
    </section>
  )
}
