import { useEffect, useState } from 'react'
import api from '../api/client'

export default function LiveMapPage() {
  const [drivers, setDrivers] = useState([])
  useEffect(() => {
    const load = () => api.get('/admin/drivers/live').then((res) => setDrivers(res.data)).catch(() => {})
    load()
    const t = setInterval(load, 10000)
    return () => clearInterval(t)
  }, [])

  return (
    <section>
      <h1>السائقون النشطون الآن</h1>
      <table>
        <thead><tr><th>السائق</th><th>الموقع</th><th>الوقت</th></tr></thead>
        <tbody>
          {drivers.map((d, i) => (
            <tr key={i}><td>{d.driver_name}</td><td>{d.lat},{d.lng}</td><td>{d.captured_at}</td></tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
