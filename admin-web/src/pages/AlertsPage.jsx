import { useEffect, useState } from 'react'
import api from '../api/client'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  useEffect(() => {
    api.get('/admin/alerts').then((res) => setAlerts(res.data)).catch(() => {})
  }, [])

  return (
    <section>
      <h1>التنبيهات</h1>
      {alerts.length === 0 && <p>لا توجد تنبيهات</p>}
      <table>
        <thead><tr><th>النوع</th><th>الشدة</th><th>الرسالة</th><th>الوقت</th></tr></thead>
        <tbody>
          {alerts.map((a) => <tr key={a.id}><td>{a.type}</td><td>{a.severity}</td><td>{a.message}</td><td>{a.created_at}</td></tr>)}
        </tbody>
      </table>
    </section>
  )
}
