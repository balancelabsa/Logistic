import { useState } from 'react'
import api from '../api/client'

export default function ReportsPage() {
  const [driverId, setDriverId] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [error, setError] = useState('')

  const download = async () => {
    try {
      const res = await api.get('/admin/reports/route-pdf', {
        params: { driver_id: driverId, date },
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      window.open(url, '_blank')
    } catch {
      setError('تعذر تصدير التقرير، تحقق من البيانات والصلاحيات')
    }
  }

  return (
    <section>
      <h1>التقارير</h1>
      <p>تقرير PDF قابل للطباعة.</p>
      <input placeholder="driver_id" value={driverId} onChange={(e) => setDriverId(e.target.value)} />
      <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      <button onClick={download}>تصدير PDF</button>
      {error && <p className="error">{error}</p>}
    </section>
  )
}
