import { useEffect, useState } from 'react'
import api from '../api/client'

export default function VisitsComparisonPage() {
  const [driverId, setDriverId] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [rows, setRows] = useState([])
  const [drivers, setDrivers] = useState([])

  useEffect(() => {
    api.get('/admin/drivers').then((r) => setDrivers(r.data)).catch(() => {})
  }, [])

  const load = async () => {
    if (!driverId) return
    const res = await api.get('/admin/drivers/route-history', { params: { driver_id: driverId, date } })
    setRows(res.data.visits)
  }

  return (
    <section>
      <h1>المخطط مقابل الفعلي</h1>
      <div className="filters">
        <select value={driverId} onChange={(e) => setDriverId(e.target.value)}>
          <option value="">اختر السائق</option>
          {drivers.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <button onClick={load}>تحميل</button>
      </div>
      {rows.length === 0 ? <p>لا توجد زيارات في هذا اليوم</p> : (
        <table>
          <thead><tr><th>الجهة</th><th>الوقت المخطط</th><th>وقت الوصول</th><th>وقت المغادرة</th><th>الحالة</th><th>مدة التأخير</th><th>الملاحظة</th><th>صورة الإثبات</th></tr></thead>
          <tbody>
            {rows.map((v) => <tr key={v.visit_id}><td>{v.customer_name}</td><td>{v.planned_at}</td><td>{v.actual_arrival_at||'-'}</td><td>{v.actual_departure_at||'-'}</td><td>{v.status}</td><td>{v.delay_minutes}</td><td>{v.driver_note||'-'}</td><td>{v.proof_image_url ? <a href={(import.meta.env.VITE_API_URL||'http://localhost:8000')+v.proof_image_url} target="_blank">عرض</a> : '-'}</td></tr>)}
          </tbody>
        </table>
      )}
    </section>
  )
}
