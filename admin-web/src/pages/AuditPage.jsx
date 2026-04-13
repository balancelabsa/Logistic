import { useEffect, useState } from 'react'
import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000' })

export default function AuditPage() {
  const [rows, setRows] = useState([])
  useEffect(() => {
    api.get('/admin/audit-trail').then((res) => setRows(res.data)).catch(() => {})
  }, [])

  return (
    <section>
      <h1>سجل التدقيق</h1>
      <table>
        <thead><tr><th>الإجراء</th><th>نوع الكيان</th><th>المعرف</th><th>الوقت</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}><td>{r.action}</td><td>{r.entity_type}</td><td>{r.entity_id}</td><td>{r.created_at}</td></tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
