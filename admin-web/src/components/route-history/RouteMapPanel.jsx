import { useEffect, useMemo, useState } from 'react'
import { GoogleMap, InfoWindow, Marker, Polyline, useJsApiLoader } from '@react-google-maps/api'

const fallbackCenter = { lat: 24.7136, lng: 46.6753 }

export default function RouteMapPanel({
  apiKey,
  points,
  stops,
  visits,
  playbackIndex,
  mapInstance,
  setMapInstance,
  setMapReady,
  selectedVisit,
  selectedStop,
}) {
  const [activeInfo, setActiveInfo] = useState(null)
  const { isLoaded } = useJsApiLoader({ googleMapsApiKey: apiKey || '' })

  const path = useMemo(() => (points || []).map((p) => ({ lat: Number(p.latitude), lng: Number(p.longitude), t: p.recorded_at })), [points])
  const validPath = path.filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lng))

  const selectedCenter = selectedVisit?.latitude && selectedVisit?.longitude
    ? { lat: Number(selectedVisit.latitude), lng: Number(selectedVisit.longitude) }
    : selectedStop?.latitude && selectedStop?.longitude
      ? { lat: Number(selectedStop.latitude), lng: Number(selectedStop.longitude) }
      : validPath[0] || fallbackCenter

  useEffect(() => {
    if (!mapInstance || !window.google?.maps || validPath.length === 0) return
    const bounds = new window.google.maps.LatLngBounds()
    validPath.forEach((p) => bounds.extend({ lat: p.lat, lng: p.lng }))
    ;(stops || []).forEach((s) => Number.isFinite(Number(s.latitude)) && Number.isFinite(Number(s.longitude)) && bounds.extend({ lat: Number(s.latitude), lng: Number(s.longitude) }))
    ;(visits || []).forEach((v) => Number.isFinite(Number(v.latitude)) && Number.isFinite(Number(v.longitude)) && bounds.extend({ lat: Number(v.latitude), lng: Number(v.longitude) }))
    if (!bounds.isEmpty()) mapInstance.fitBounds(bounds)
  }, [mapInstance, validPath, stops, visits])

  if (!apiKey) return <div className="state-box">يرجى إضافة مفتاح Google Maps API في إعدادات البيئة</div>
  if (!isLoaded) return <div className="state-box">جاري تحميل الخريطة...</div>

  return (
    <GoogleMap
      mapContainerStyle={{ width: '100%', height: '460px' }}
      center={selectedCenter}
      zoom={10}
      onLoad={(map) => { setMapInstance(map); setMapReady(true) }}
      onUnmount={() => { setMapReady(false); setMapInstance(null) }}
    >
      {validPath.length > 1 && <Polyline path={validPath} options={{ strokeColor: '#0b79d0', strokeWeight: 4 }} />}
      {validPath.length > 0 && <Marker position={validPath[0]} label="بداية" onClick={() => setActiveInfo({ pos: validPath[0], text: 'بداية المسار' })} />}
      {validPath.length > 1 && <Marker position={validPath[validPath.length - 1]} label="نهاية" onClick={() => setActiveInfo({ pos: validPath[validPath.length - 1], text: 'نهاية المسار' })} />}

      {(stops || []).map((s, i) => Number.isFinite(Number(s.latitude)) && Number.isFinite(Number(s.longitude)) ? (
        <Marker
          key={`stop-${i}`}
          position={{ lat: Number(s.latitude), lng: Number(s.longitude) }}
          label="توقف"
          icon="http://maps.google.com/mapfiles/ms/icons/orange-dot.png"
          onClick={() => setActiveInfo({ pos: { lat: Number(s.latitude), lng: Number(s.longitude) }, text: `توقف: ${s.duration_minutes || '-'} دقيقة` })}
        />
      ) : null)}

      {(visits || []).map((v) => Number.isFinite(Number(v.latitude)) && Number.isFinite(Number(v.longitude)) ? (
        <Marker
          key={v.visit_id}
          position={{ lat: Number(v.latitude), lng: Number(v.longitude) }}
          label={v.status === 'delayed' ? 'متأخرة' : 'زيارة'}
          icon={v.status === 'delayed' ? 'http://maps.google.com/mapfiles/ms/icons/red-dot.png' : 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'}
          onClick={() => setActiveInfo({ pos: { lat: Number(v.latitude), lng: Number(v.longitude) }, text: `${v.customer_name} (${v.status || '-'})` })}
        />
      ) : null)}

      {validPath[playbackIndex] && <Marker position={validPath[playbackIndex]} label="🚚" />}

      {activeInfo?.pos && (
        <InfoWindow position={activeInfo.pos} onCloseClick={() => setActiveInfo(null)}>
          <div>{activeInfo.text}</div>
        </InfoWindow>
      )}
    </GoogleMap>
  )
}
