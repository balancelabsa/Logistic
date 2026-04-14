import { useEffect, useState } from 'react'
import api from '../api/client'

export default function AuditPage() {
  const [rows, setRows] = useState([])
  useEffect(() => {
    api.get('/admin/audit-trail').then((res) => setRows(res.data)).catch(() => {})
  }, [])

  return (
    <section>
      <h1>سجل التدقيق</h1>
      <table>
        <thead><tr><th>الإجراء</th><th>النوع</th><th>الكيان</th><th>الوقت</th></tr></thead>
        <tbody>
          {rows.map((r) => <tr key={r.id}><td>{r.action}</td><td>{r.entity_type}</td><td>{r.entity_id}</td><td>{r.created_at}</td></tr>)}
        </tbody>
      </table>
    </section>
  )
}
