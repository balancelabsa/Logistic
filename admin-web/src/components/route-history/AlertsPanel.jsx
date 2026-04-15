const safe = (v) => (v === null || v === undefined || v === '' ? '-' : v)

export default function AlertsPanel({ alerts, onSelectAlert, selectedAlertIndex }) {
  return (
    <section>
      <h3>التنبيهات</h3>
      {alerts.length === 0 ? <p>لا توجد تنبيهات</p> : (
        <table>
          <thead><tr><th>النوع</th><th>الشدة</th><th>الرسالة</th><th>الوقت</th><th>الحالة</th></tr></thead>
          <tbody>
            {alerts.map((a, idx) => (
              <tr key={`${a.created_at}-${idx}`} className={selectedAlertIndex === idx ? 'row-active' : ''} onClick={() => onSelectAlert?.(a, idx)}>
                <td>{safe(a.type)}</td>
                <td>{safe(a.severity)}</td>
                <td>{safe(a.message)}</td>
                <td>{safe(a.created_at)}</td>
                <td>{safe(a.status || '-')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
