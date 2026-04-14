import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import RouteFilters from '../components/route-history/RouteFilters'
import RouteSummaryCards from '../components/route-history/RouteSummaryCards'
import RouteMapPanel from '../components/route-history/RouteMapPanel'
import PlaybackControls from '../components/route-history/PlaybackControls'
import VisitsTable from '../components/route-history/VisitsTable'
import StopsTable from '../components/route-history/StopsTable'
import AlertsPanel from '../components/route-history/AlertsPanel'
import EmptyState from '../components/route-history/EmptyState'
import ErrorState from '../components/route-history/ErrorState'

const safeArray = (arr) => (Array.isArray(arr) ? arr : [])

function toCsv(rows, headers) {
  const escape = (v) => `"${String(v ?? '-').replaceAll('"', '""')}"`
  return [headers.join(','), ...rows.map((row) => headers.map((h) => escape(row[h])).join(','))].join('\n')
}

export default function RouteHistoryPage() {
  const [drivers, setDrivers] = useState([])
  const [filters, setFilters] = useState({
    driverId: '',
    date: new Date().toISOString().slice(0, 10),
    branch: '',
    alertType: '',
    visitStatus: '',
  })

  const [rawData, setRawData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [hasSearched, setHasSearched] = useState(false)

  const [selectedVisit, setSelectedVisit] = useState(null)
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [selectedStop, setSelectedStop] = useState(null)

  const [mapReady, setMapReady] = useState(false)
  const [mapInstance, setMapInstance] = useState(null)

  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [index, setIndex] = useState(0)

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY

  useEffect(() => {
    api.get('/admin/drivers').then((r) => setDrivers(safeArray(r.data))).catch(() => setDrivers([]))
  }, [])

  const points = safeArray(rawData?.points)
  const visits = safeArray(rawData?.visits)
  const stops = safeArray(rawData?.stops)
  const alerts = safeArray(rawData?.alerts)

  const filteredVisits = useMemo(
    () => visits.filter((v) => (filters.visitStatus ? v.status === filters.visitStatus : true)),
    [visits, filters.visitStatus],
  )
  const filteredAlerts = useMemo(
    () => alerts.filter((a) => (filters.alertType ? a.type === filters.alertType : true)),
    [alerts, filters.alertType],
  )

  useEffect(() => {
    if (!playing || points.length === 0) return
    if (index >= points.length - 1) {
      setPlaying(false)
      return
    }
    const timer = setTimeout(() => setIndex((i) => Math.min(i + 1, points.length - 1)), 1000 / speed)
    return () => clearTimeout(timer)
  }, [playing, index, points.length, speed])

  const load = async () => {
    if (!filters.driverId) return
    setHasSearched(true)
    setLoading(true)
    setError('')
    setRawData(null)
    setSelectedVisit(null)
    setSelectedAlert(null)
    setSelectedStop(null)
    setIndex(0)
    setPlaying(false)

    try {
      const res = await api.get('/admin/drivers/route-history', {
        params: { driver_id: filters.driverId, date: filters.date },
      })
      setRawData(res.data || null)
    } catch {
      setError('حدث خطأ أثناء تحميل بيانات المسار')
    } finally {
      setLoading(false)
    }
  }

  const summary = useMemo(() => {
    const completed = filteredVisits.filter((v) => ['departed', 'arrived'].includes(v.status)).length
    const delayed = filteredVisits.filter((v) => v.status === 'delayed').length
    const withoutDeparture = filteredVisits.filter((v) => v.actual_arrival_at && !v.actual_departure_at).length
    return {
      totalPoints: rawData?.total_points || 0,
      startedAt: rawData?.started_at || '-',
      endedAt: rawData?.ended_at || '-',
      durationMinutes: rawData?.total_duration_minutes || 0,
      distanceKm: rawData?.total_distance_km || 0,
      averageSpeed: rawData?.average_speed_kmh || 0,
      totalStops: stops.length || 0,
      totalAlerts: filteredAlerts.length || 0,
      totalPlannedVisits: filteredVisits.length || 0,
      completedVisits: completed,
      delayedVisits: delayed,
      withoutDeparture,
    }
  }, [rawData, stops.length, filteredAlerts.length, filteredVisits])

  const currentTimestamp = points[index]?.recorded_at || '-'

  const exportCsv = (type) => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const dataByType = {
      visits: filteredVisits.map((v) => ({ ...v, proof_image_url: v.proof_image_url ? `${baseUrl}${v.proof_image_url}` : '-' })),
      stops,
      alerts: filteredAlerts,
    }
    const rows = dataByType[type] || []
    if (rows.length === 0) return
    const headers = Object.keys(rows[0])
    const blob = new Blob([toCsv(rows, headers)], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${type}-${filters.driverId}-${filters.date}.csv`
    link.click()
  }

  return (
    <section>
      <h1>مسار السائقين</h1>
      <RouteFilters
        drivers={drivers}
        filters={filters}
        setFilters={setFilters}
        onSearch={load}
        loading={loading}
        alertTypes={[...new Set(alerts.map((a) => a.type).filter(Boolean))]}
        visitStatuses={[...new Set(visits.map((v) => v.status).filter(Boolean))]}
        branchOptions={[]}
      />

      <div className="controls">
        <button onClick={() => window.print()} disabled={!rawData}>طباعة</button>
        <button onClick={() => exportCsv('visits')} disabled={!filteredVisits.length}>تصدير CSV للزيارات</button>
        <button onClick={() => exportCsv('stops')} disabled={!stops.length}>تصدير CSV للتوقفات</button>
        <button onClick={() => exportCsv('alerts')} disabled={!filteredAlerts.length}>تصدير CSV للتنبيهات</button>
      </div>

      {!hasSearched && <EmptyState message="اختر السائق والتاريخ ثم اضغط تحميل" />}
      {loading && <EmptyState message="جاري تحميل بيانات المسار..." />}
      {!!error && !loading && <ErrorState message={error} onRetry={load} />}
      {hasSearched && !loading && !error && rawData && points.length === 0 && <EmptyState message="لا توجد بيانات مسار لهذا السائق في التاريخ المحدد" />}

      {hasSearched && !loading && !error && rawData && (
        <>
          <RouteSummaryCards summary={summary} />

          <RouteMapPanel
            apiKey={apiKey}
            points={points}
            stops={stops}
            visits={filteredVisits}
            playbackIndex={index}
            mapInstance={mapInstance}
            setMapInstance={setMapInstance}
            setMapReady={setMapReady}
            selectedVisit={selectedVisit}
            selectedStop={selectedStop}
          />

          <PlaybackControls
            playing={playing}
            speed={speed}
            index={index}
            total={points.length}
            currentTimestamp={currentTimestamp}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onReset={() => {
              setPlaying(false)
              setIndex(0)
            }}
            setSpeed={setSpeed}
          />

          <VisitsTable
            visits={filteredVisits}
            selectedVisitId={selectedVisit?.visit_id}
            onSelectVisit={(v) => setSelectedVisit(v)}
          />

          <StopsTable
            stops={stops}
            selectedStopIndex={selectedStop?.idx}
            onSelectStop={(s, idx) => setSelectedStop({ ...s, idx })}
          />

          <AlertsPanel
            alerts={filteredAlerts}
            selectedAlertIndex={selectedAlert?.idx}
            onSelectAlert={(a, idx) => setSelectedAlert({ ...a, idx })}
          />

          <div className="state-box small">
            حالة الخريطة: {mapReady ? 'جاهزة' : 'غير جاهزة'}
          </div>
        </>
      )}
    </section>
  )
}
