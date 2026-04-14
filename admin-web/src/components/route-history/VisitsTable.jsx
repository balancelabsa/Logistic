const safe = (v) => (v === null || v === undefined || v === '' ? '-' : v)

export default function VisitsTable({ visits, onSelectVisit, selectedVisitId }) {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  return (
    <section>
      <h3>مقارنة الزيارات (المخطط مقابل الفعلي)</h3>
      {visits.length === 0 ? <p>لا توجد زيارات في هذا اليوم</p> : (
        <table>
          <thead>
            <tr>
              <th>الجهة</th><th>الوقت المخطط</th><th>وقت الوصول</th><th>وقت المغادرة</th>
              <th>الحالة</th><th>مدة التأخير</th><th>مدة التواجد</th><th>الملاحظة</th><th>صورة الإثبات</th>
            </tr>
          </thead>
          <tbody>
            {visits.map((v) => (
              <tr key={v.visit_id} className={selectedVisitId === v.visit_id ? 'row-active' : ''} onClick={() => onSelectVisit?.(v)}>
                <td>{safe(v.customer_name)}</td>
                <td>{safe(v.planned_at)}</td>
                <td>{safe(v.actual_arrival_at)}</td>
                <td>{safe(v.actual_departure_at)}</td>
                <td>{safe(v.status)}</td>
                <td>{safe(v.delay_minutes)}</td>
                <td>{safe(v.stay_duration_minutes)}</td>
                <td>{safe(v.driver_note)}</td>
                <td>{v.proof_image_url ? <a href={`${baseUrl}${v.proof_image_url}`} target="_blank" rel="noreferrer">عرض</a> : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
