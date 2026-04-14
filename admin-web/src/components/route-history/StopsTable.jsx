const safe = (v) => (v === null || v === undefined || v === '' ? '-' : v)

export default function StopsTable({ stops, onSelectStop, selectedStopIndex }) {
  return (
    <section>
      <h3>التوقفات</h3>
      {stops.length === 0 ? <p>لا توجد توقفات</p> : (
        <table>
          <thead><tr><th>بداية التوقف</th><th>نهاية التوقف</th><th>مدة التوقف</th><th>الموقع</th><th>التصنيف</th></tr></thead>
          <tbody>
            {stops.map((s, idx) => (
              <tr key={`${s.started_at}-${idx}`} className={selectedStopIndex === idx ? 'row-active' : ''} onClick={() => onSelectStop?.(s, idx)}>
                <td>{safe(s.started_at)}</td>
                <td>{safe(s.ended_at)}</td>
                <td>{safe(s.duration_minutes)} دقيقة</td>
                <td>{safe(s.latitude)}, {safe(s.longitude)}</td>
                <td>{safe(s.classification || '-')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
