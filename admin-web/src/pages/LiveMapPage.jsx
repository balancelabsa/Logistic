import { useEffect, useState } from 'react'
import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000' })

export default function LiveMapPage() {
  const [drivers, setDrivers] = useState([])

  useEffect(() => {
    api.get('/admin/drivers/live').then((res) => setDrivers(res.data)).catch(() => {})
  }, [])

  return (
    <section>
      <h1>المراقبة الحية</h1>
      <p>عرض مباشر لآخر إحداثيات السائقين أثناء الوردية النشطة.</p>
      <table>
        <thead>
          <tr><th>السائق</th><th>خط العرض</th><th>خط الطول</th><th>الوقت</th></tr>
        </thead>
        <tbody>
          {drivers.map((d) => (
            <tr key={`${d.driver_id}-${d.captured_at}`}>
              <td>{d.driver_name}</td><td>{d.lat}</td><td>{d.lng}</td><td>{d.captured_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
