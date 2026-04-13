import { useEffect, useState } from 'react'
import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000' })

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  useEffect(() => {
    api.get('/admin/alerts').then((res) => setAlerts(res.data)).catch(() => {})
  }, [])

  return (
    <section>
      <h1>التنبيهات</h1>
      <ul>
        {alerts.map((a) => (
          <li key={a.id}>{a.type} - {a.message}</li>
        ))}
      </ul>
    </section>
  )
}
