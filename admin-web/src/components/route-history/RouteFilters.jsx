export default function RouteFilters({
  drivers,
  filters,
  setFilters,
  onSearch,
  loading,
  alertTypes,
  visitStatuses,
  branchOptions,
}) {
  return (
    <div className="filters route-filters">
      <select value={filters.driverId} onChange={(e) => setFilters((s) => ({ ...s, driverId: e.target.value }))}>
        <option value="">اختر السائق</option>
        {drivers.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
      </select>
      <input type="date" value={filters.date} onChange={(e) => setFilters((s) => ({ ...s, date: e.target.value }))} />
      <select value={filters.branch} onChange={(e) => setFilters((s) => ({ ...s, branch: e.target.value }))}>
        <option value="">كل الفروع</option>
        {branchOptions.map((b) => <option key={b} value={b}>{b}</option>)}
      </select>
      <select value={filters.alertType} onChange={(e) => setFilters((s) => ({ ...s, alertType: e.target.value }))}>
        <option value="">كل التنبيهات</option>
        {alertTypes.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      <select value={filters.visitStatus} onChange={(e) => setFilters((s) => ({ ...s, visitStatus: e.target.value }))}>
        <option value="">كل حالات الزيارات</option>
        {visitStatuses.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      <button disabled={loading || !filters.driverId} onClick={onSearch}>{loading ? 'جاري التحميل...' : 'تحميل'}</button>
    </div>
  )
}
