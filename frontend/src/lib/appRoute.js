/**
 * Lightweight page/week query sync (no router dependency).
 */
const PAGES = new Set(['dashboard', 'charts', 'logs', 'calibration', 'settings'])

export function readPageFromUrl() {
  try {
    const page = new URLSearchParams(window.location.search).get('page')
    if (PAGES.has(page)) return page
  } catch {
    /* ignore */
  }
  return 'dashboard'
}

export function syncUrl({ page, week }) {
  try {
    const url = new URL(window.location.href)
    if (PAGES.has(page)) url.searchParams.set('page', page)
    if (week) url.searchParams.set('week', week)
    else url.searchParams.delete('week')
    window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`)
  } catch {
    /* ignore */
  }
}
