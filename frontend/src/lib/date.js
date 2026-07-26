/**
 * Small helpers for dates and week labels (e.g. 2026-W24).
 */
export function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

export function dateToWeekLabel(isoDate) {
  const d = new Date(`${isoDate}T12:00:00`)
  const day = (d.getDay() + 6) % 7
  d.setDate(d.getDate() - day + 3)
  const jan4 = new Date(d.getFullYear(), 0, 4)
  const week =
    1 +
    Math.round(
      ((d - jan4) / 86400000 - 3 + ((jan4.getDay() + 6) % 7)) / 7
    )
  return `${d.getFullYear()}-W${String(week).padStart(2, '0')}`
}

export function formatDateTime(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString()
}
