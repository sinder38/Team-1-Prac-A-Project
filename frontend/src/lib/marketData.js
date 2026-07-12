/**
 * Example OHLC market data for the price charts (SPX, NDX, IWM, etc.).
 * Deterministic so charts stay stable between reloads. Price levels match the
 * agent example data (e.g. SPX last close ~7,554, Gold ~4,238).
 *
 * TODO (backend task): replace buildHistory() with real yfinance OHLC served by
 * the backend, e.g. GET /api/market/history?symbol=SPX. The shape returned here
 * (candles / ema8 / ema21 / volume / stats) is what the chart expects.
 */

export const INSTRUMENTS = [
  { symbol: 'SPX', name: 'S&P 500', yahoo: '^GSPC', last: 7554, vol: 0.008, drift: 0.0010, decimals: 0, baseVol: 2.6e9 },
  { symbol: 'NDX', name: 'Nasdaq 100', yahoo: '^NDX', last: 25320, vol: 0.011, drift: 0.0014, decimals: 0, baseVol: 9.0e8 },
  { symbol: 'IWM', name: 'Russell 2000', yahoo: 'IWM', last: 244.8, vol: 0.012, drift: 0.0003, decimals: 2, baseVol: 3.2e7 },
  { symbol: 'GOLD', name: 'Gold (Spot)', yahoo: 'GC=F', last: 4238.8, vol: 0.009, drift: -0.0006, decimals: 1, baseVol: 2.1e5 },
  { symbol: 'WTI', name: 'Crude Oil (WTI)', yahoo: 'CL=F', last: 84.88, vol: 0.018, drift: -0.0012, decimals: 2, baseVol: 4.5e5 },
  { symbol: 'DXY', name: 'US Dollar Index', yahoo: 'DX-Y.NYB', last: 99.75, vol: 0.004, drift: -0.0002, decimals: 2, baseVol: 0 },
]

function mulberry32(seed) {
  let a = seed >>> 0
  return function () {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function seedFor(symbol) {
  let h = 2166136261
  for (let i = 0; i < symbol.length; i++) {
    h ^= symbol.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

/** Generate `n` weekday (Mon-Fri) ISO dates ending at `endIso`. */
function weekdayDates(n, endIso) {
  const dates = []
  const d = new Date(`${endIso}T00:00:00`)
  while (dates.length < n) {
    const day = d.getDay()
    if (day !== 0 && day !== 6) dates.push(d.toISOString().slice(0, 10))
    d.setDate(d.getDate() - 1)
  }
  return dates.reverse()
}

function ema(values, period) {
  const k = 2 / (period + 1)
  let prev = values[0]
  return values.map((v, i) => {
    if (i === 0) return v
    prev = v * k + prev * (1 - k)
    return prev
  })
}

function roundTo(v, decimals) {
  const f = 10 ** decimals
  return Math.round(v * f) / f
}

export function buildHistory(symbol, n = 130) {
  const inst = INSTRUMENTS.find(i => i.symbol === symbol) || INSTRUMENTS[0]
  const rand = mulberry32(seedFor(inst.symbol))
  const dates = weekdayDates(n, '2026-06-05')

  // Random walk of closes, then normalized so the final close equals inst.last.
  const raw = [100]
  for (let i = 1; i < n; i++) {
    const shock = (rand() * 2 - 1) * inst.vol
    raw.push(raw[i - 1] * (1 + inst.drift + shock))
  }
  const scale = inst.last / raw[n - 1]
  const closes = raw.map(v => v * scale)

  const candles = []
  const volume = []
  for (let i = 0; i < n; i++) {
    const close = closes[i]
    const prevClose = i === 0 ? close : closes[i - 1]
    const gap = (rand() * 2 - 1) * inst.vol * 0.3
    const open = i === 0 ? close * (1 - inst.vol * 0.2) : prevClose * (1 + gap)
    const high = Math.max(open, close) * (1 + rand() * inst.vol * 0.7)
    const low = Math.min(open, close) * (1 - rand() * inst.vol * 0.7)
    const up = close >= open

    candles.push({
      time: dates[i],
      open: roundTo(open, inst.decimals),
      high: roundTo(high, inst.decimals),
      low: roundTo(low, inst.decimals),
      close: roundTo(close, inst.decimals),
    })

    if (inst.baseVol > 0) {
      volume.push({
        time: dates[i],
        value: Math.round(inst.baseVol * (0.6 + rand() * 0.9)),
        color: up ? 'rgba(22,163,74,0.35)' : 'rgba(220,38,38,0.35)',
      })
    }
  }

  const e8 = ema(closes, 8)
  const e21 = ema(closes, 21)
  const ema8 = dates.map((time, i) => ({ time, value: roundTo(e8[i], inst.decimals) }))
  const ema21 = dates.map((time, i) => ({ time, value: roundTo(e21[i], inst.decimals) }))

  const last = candles[n - 1].close
  const prev = candles[n - 2].close
  const change = roundTo(last - prev, inst.decimals)
  const changePct = roundTo(((last - prev) / prev) * 100, 2)
  const periodHigh = Math.max(...candles.map(c => c.high))
  const periodLow = Math.min(...candles.map(c => c.low))

  return {
    symbol: inst.symbol,
    name: inst.name,
    yahoo: inst.yahoo,
    decimals: inst.decimals,
    candles,
    ema8,
    ema21,
    volume,
    stats: {
      last,
      change,
      changePct,
      periodHigh: roundTo(periodHigh, inst.decimals),
      periodLow: roundTo(periodLow, inst.decimals),
      ema8: ema8[n - 1].value,
      ema21: ema21[n - 1].value,
      aboveEmas: last > ema8[n - 1].value && last > ema21[n - 1].value,
    },
  }
}
