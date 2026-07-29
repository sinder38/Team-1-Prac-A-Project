/**
 * Market price history (yfinance via backend).
 */
import { INSTRUMENTS } from '../lib/marketData'

export function getInstruments() {
  return INSTRUMENTS.map(({ symbol, name, yahoo }) => ({ symbol, name, yahoo }))
}

export async function getMarketHistory(symbol, opts = {}) {
  const qs = new URLSearchParams({ symbol })
  if (opts.days) qs.set('days', String(opts.days))
  if (opts.endDate) qs.set('end_date', opts.endDate)
  const resp = await fetch(`/market/history?${qs}`)
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    throw new Error(body.error || `Market history failed (${resp.status})`)
  }
  return resp.json()
}
