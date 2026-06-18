/**
 * Market price history for the charts.
 * TODO (backend task): replace example data with GET /api/market/history?symbol=SPX
 * (backend should proxy yfinance OHLC). See ../lib/marketData.js for the shape.
 */
import { INSTRUMENTS, buildHistory } from '../lib/marketData'

export function getInstruments() {
  return INSTRUMENTS.map(({ symbol, name, yahoo }) => ({ symbol, name, yahoo }))
}

export async function getMarketHistory(symbol) {
  // TODO: GET /api/market/history?symbol=SPX
  return buildHistory(symbol)
}
