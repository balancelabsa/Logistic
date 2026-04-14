import { useEffect, useMemo, useState } from 'react'
import { GoogleMap, Marker, Polyline, useJsApiLoader } from '@react-google-maps/api'
import api from '../api/client'

export default function RouteHistoryPage() {
  const [drivers, setDrivers] = useState([])
  const [driverId, setDriverId] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [data, setData] = useState(null)
  const [index, setIndex] = useState(0)
  const [speed, setSpeed] = useState(1)
  const [playing, setPlaying] = useState(false)
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY

  const { isLoaded } = useJsApiLoader({ googleMapsApiKey: apiKey || '' })

  useEffect(() => {
    api.get('/admin/drivers').then((r) => setDrivers(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (!playing || !data?.points?.length) return
    const t = setInterval(() => setIndex((i) => Math.min(i + 1, data.points.length - 1)), 1000 / speed)
    return () => clearInterval(t)
  }, [playing, speed, data])

  const load = async () => {
    if (!driverId) return
    const res = await api.get('/admin/drivers/route-history', { params: { driver_id: driverId, date } })
    setData(res.data)
    setIndex(0)
    setPlaying(false)
  }

  const path = useMemo(() => (data?.points || []).map((p) => ({ lat: p.latitude, lng: p.longitude })), [data])

  if (!apiKey) return <p>يرجى إضافة مفتاح Google Maps API في إعدادات البيئة</p>

  return (
    <section>
      <h1>مسار السائقين</h1>
      <div className="filters">
        <select value={driverId} onChange={(e) => setDriverId(e.target.value)}>
          <option value="">اختر السائق</option>
          {drivers.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <button onClick={load}>تحميل</button>
      </div>

      {!data && <p>لا توجد بيانات مسار لهذا السائق في التاريخ المحدد</p>}
      {data && (
        <>
          <div className="grid">
            <div className="card">عدد النقاط: {data.total_points}</div>
            <div className="card">وقت البداية: {data.started_at || '-'}</div>
            <div className="card">وقت النهاية: {data.ended_at || '-'}</div>
            <div className="card">مدة المسار: {data.total_duration_minutes} دقيقة</div>
            <div className="card">المسافة المقطوعة: {data.total_distance_km} كم</div>
            <div className="card">متوسط السرعة: {data.average_speed_kmh} كم/س</div>
            <div className="card">عدد التوقفات: {data.total_stops}</div>
            <div className="card">عدد التنبيهات: {data.alerts.length}</div>
          </div>

          {isLoaded && (
            <GoogleMap mapContainerStyle={{ width: '100%', height: '420px' }} center={path[0] || { lat: 24.7, lng: 46.7 }} zoom={10}>
              {path.length > 0 && <Marker position={path[0]} label="بداية" />}
              {path.length > 1 && <Marker position={path[path.length - 1]} label="نهاية" />}
              {path.length > 1 && <Polyline path={path} options={{ strokeColor: '#0b79d0', strokeWeight: 4 }} />}
              {data.stops.map((s, i) => <Marker key={i} position={{ lat: s.latitude, lng: s.longitude }} label="توقف" />)}
              {data.visits.map((v) => v.latitude && v.longitude ? <Marker key={v.visit_id} position={{ lat: v.latitude, lng: v.longitude }} label="زيارة" /> : null)}
              {path[index] && <Marker position={path[index]} label="🚚" />}
            </GoogleMap>
          )}

          <div className="controls">
            <button onClick={() => setPlaying(true)}>تشغيل</button>
            <button onClick={() => setPlaying(false)}>إيقاف مؤقت</button>
            <button onClick={() => { setIndex(0); setPlaying(false) }}>إعادة</button>
            <button onClick={() => setSpeed(1)}>سرعة 1x</button>
            <button onClick={() => setSpeed(2)}>سرعة 2x</button>
            <button onClick={() => setSpeed(4)}>سرعة 4x</button>
          </div>
        </>
      )}
    </section>
  )
}
