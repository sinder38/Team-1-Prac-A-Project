/**
 * Market price history for the charts (yfinance via backend).
 */
import { INSTRUMENTS } from '../lib/marketData'

export function getInstruments() {
  return INSTRUMENTS.map(({ symbol, name, yahoo }) => ({ symbol, name, yahoo }))
}

export async function getMarketHistory(symbol) {
  const resp = await fetch(`/market/history?symbol=${encodeURIComponent(symbol)}`)
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    throw new Error(body.error || `Market history failed (${resp.status})`)
  }
  return resp.json()
}
