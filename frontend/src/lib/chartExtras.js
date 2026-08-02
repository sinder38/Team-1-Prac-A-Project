/**
 * Chart helpers for the Charts page.
 */

export function rebaseCloses(candles) {
  if (!Array.isArray(candles) || !candles.length) return []
  const base = Number(candles[0].close)
  if (!Number.isFinite(base) || base === 0) return []
  return candles.map(c => ({
    time: c.time,
    value: Math.round((100 * Number(c.close) / base) * 100) / 100,
  }))
}

export function periodChangePct(candles) {
  if (!Array.isArray(candles) || candles.length < 2) return null
  const first = Number(candles[0].close)
  const last = Number(candles[candles.length - 1].close)
  if (!Number.isFinite(first) || !Number.isFinite(last) || first === 0) return null
  return Math.round(((last - first) / first) * 10000) / 100
}

export function parsePctRange(text) {
  if (text == null || text === '' || text === '—') return null
  if (typeof text === 'object') {
    const low = text.low === '' || text.low == null ? null : Number(text.low)
    const high = text.high === '' || text.high == null ? null : Number(text.high)
    if (!Number.isFinite(low) || !Number.isFinite(high)) return null
    return { low, high }
  }
  const m = String(text).match(/([+-]?\d+(?:\.\d+)?)\s*%?\s*(?:to|–|-|—)\s*([+-]?\d+(?:\.\d+)?)\s*%?/i)
  if (!m) return null
  return { low: Number(m[1]), high: Number(m[2]) }
}

/** Final Prediction range only — never invents an LLM envelope. */
export function predictedRangeForSymbol(symbol, { finalPrediction } = {}) {
  const key = String(symbol || '').toLowerCase()
  if (!['spx', 'ndx', 'iwm'].includes(key)) return null
  const asset = finalPrediction?.form?.assets?.[key]
  if (!asset) return null

  const range = parsePctRange({ low: asset.rangeLow, high: asset.rangeHigh })
    || parsePctRange(asset.range)
  if (!range) return null
  return { ...range, source: 'Final Prediction', direction: asset.direction }
}

export function rangeHit(pred, actualPct) {
  if (!pred || actualPct == null || Number.isNaN(Number(actualPct))) return null
  const a = Number(actualPct)
  return a >= Math.min(pred.low, pred.high) && a <= Math.max(pred.low, pred.high)
}

export function technicalContext(technical, symbol) {
  if (!technical || !symbol) return null

  const inst = technical.instruments?.[symbol]
  if (inst) {
    return {
      lastClose: inst.last_close,
      bias: inst.trend_bias,
      support: inst.key_support,
      resistance: inst.key_resistance,
    }
  }

  const raw = technical.rawData || ''
  const block = raw.split(/\n(?=INSTRUMENT:)/).find(b => b.includes(`(${symbol})`))
  const metric = (re) => technical.metrics?.find(m => re.test(m.label))?.value

  // Archive metrics are SPX-only.
  const bias = (symbol === 'SPX' ? metric(/bias/i) : null)
    || block?.match(/TECHNICAL BIAS:\s*([^\n]+)/i)?.[1]?.trim()?.replace(/\.$/, '')
    || null

  const num = (re) => {
    const n = Number(block?.match(re)?.[1]?.replace(/,/g, ''))
    return Number.isFinite(n) ? n : undefined
  }
  let support = num(/Support 1:\s*([\d.,]+)/)
  let resistance = num(/Resistance 1:\s*([\d.,]+)/)
  const lastClose = num(/LAST CLOSE:\s*([\d.,]+)/)

  if (symbol === 'SPX' && support == null) {
    const parts = String(metric(/support/i) || '').split(/\s*[-–—]\s*/)
    const s = Number(parts[0])
    const r = Number(parts[1])
    if (Number.isFinite(s)) support = s
    if (Number.isFinite(r)) resistance = r
  }

  if (!bias && support == null) return null
  return { lastClose, bias: bias || '—', support, resistance }
}

function commodity(c) {
  if (!c || c.price == null || c.price === '') return null
  const change = Number(c.weekly_change)
  return {
    value: Number(c.price),
    change: Number.isFinite(change) ? change : null,
    direction: c.direction || null,
  }
}

function fromMd(raw, re) {
  const m = String(raw || '').match(re)
  if (!m) return null
  const value = Number(m[1].replace(/,/g, ''))
  const change = Number(m[2])
  return {
    value: Number.isFinite(value) ? value : null,
    change: Number.isFinite(change) ? change : null,
    direction: m[3] || null,
  }
}

function macroBias(macro, byLabel) {
  return byLabel['Macro Bias']
    || macro.macro_bias
    || String(macro.rawData || '').match(/MACRO BIAS:\s*([^\n]+)/i)?.[1]?.trim()
    || null
}

export function macroContext(macro) {
  if (!macro) return null
  const byLabel = Object.fromEntries((macro.metrics || []).map(m => [m.label, m.value]))
  const raw = macro.rawData || ''

  if (macro.yield_10y != null || macro.wti_oil || macro.fed_rate) {
    return {
      bias: macroBias(macro, byLabel),
      fedRate: macro.fed_rate ?? byLabel['Fed Rate'] ?? null,
      yield10y: macro.yield_10y != null && macro.yield_10y !== ''
        ? { value: Number(macro.yield_10y), change: null, direction: macro.yield_10y_direction || null, unit: '%' }
        : null,
      dxy: commodity(macro.dxy),
      wti: commodity(macro.wti_oil),
    }
  }

  const yMatch = String(byLabel['10Y Yield'] || '').match(/([+-]?\d+(?:\.\d+)?)/)
    || raw.match(/10-year yield:\s*([\d.]+)\s*%/i)

  return {
    bias: macroBias(macro, byLabel),
    fedRate: byLabel['Fed Rate'] || null,
    yield10y: yMatch
      ? { value: Number(yMatch[1]), change: null, direction: null, unit: '%' }
      : null,
    dxy: fromMd(raw, /DXY\s*\(Dollar\):\s*([\d,.]+),\s*weekly change\s*([+-]?[\d.]+)%,\s*direction:\s*(\w*)/i),
    wti: fromMd(raw, /WTI Crude Oil:\s*([\d,.]+),\s*weekly change\s*([+-]?[\d.]+)%,\s*direction:\s*(\w*)/i),
  }
}
