const safe = (v) => (v === null || v === undefined || v === '' ? '-' : v)

export default function RouteSummaryCards({ summary }) {
  const cards = [
    ['عدد النقاط', summary.totalPoints],
    ['وقت البداية', safe(summary.startedAt)],
    ['وقت النهاية', safe(summary.endedAt)],
    ['مدة المسار', `${safe(summary.durationMinutes)} دقيقة`],
    ['المسافة المقطوعة', `${safe(summary.distanceKm)} كم`],
    ['متوسط السرعة', `${safe(summary.averageSpeed)} كم/س`],
    ['عدد التوقفات', summary.totalStops],
    ['عدد التنبيهات', summary.totalAlerts],
    ['عدد الزيارات المخططة', summary.totalPlannedVisits],
    ['عدد الزيارات المنفذة', summary.completedVisits],
    ['عدد الزيارات المتأخرة', summary.delayedVisits],
    ['زيارات بدون مغادرة', summary.withoutDeparture],
  ]

  return (
    <div className="grid">
      {cards.map(([title, value]) => <div key={title} className="card"><h4>{title}</h4><p>{value}</p></div>)}
    </div>
  )
}
