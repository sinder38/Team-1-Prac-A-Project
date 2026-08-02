/**
 * Market Charts — yfinance OHLC/EMA, index compare, tech/macro strips, weekly actuals.
 */
import { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { PriceChart } from '../components/charts'
import { ErrorBanner } from '../components/common'
import { getActuals, getEvidenceImages, getInstruments, getMarketHistory } from '../api'
import {
  macroContext,
  periodChangePct,
  predictedRangeForSymbol,
  rangeHit,
  technicalContext,
} from '../lib/chartExtras'

const instruments = getInstruments()
const COMPARE = ['SPX', 'NDX', 'IWM']
const RANGES = [
  { id: '1M', label: '1M', days: 22 },
  { id: '3M', label: '3M', days: 66 },
  { id: '6M', label: '6M', days: 130 },
]

function fmt(value, decimals = 2) {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return Number(value).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

function fmtPct(value) {
  if (value == null || Number.isNaN(Number(value))) return '—'
  const n = Number(value)
  return `${n > 0 ? '+' : ''}${n.toFixed(2)}%`
}

function weekStem(week) {
  const m = String(week || '').match(/W\d{2}/i)
  return m ? m[0].toUpperCase() : null
}

function chipClass(active) {
  return `px-2.5 py-1 text-xs font-medium rounded-md border ${
    active
      ? 'bg-gray-900 border-gray-900 text-white'
      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
  }`
}

function StatBox({ label, value }) {
  return (
    <div className="bg-white border border-gray-200 rounded-md shadow-md px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-gray-400">{label}</p>
      <p className="text-sm font-semibold text-gray-900 mt-0.5">{value}</p>
    </div>
  )
}

StatBox.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
}

function MacroRow({ label, value, delta, note }) {
  const hasDelta = delta != null && !Number.isNaN(Number(delta))
  const tone = !hasDelta
    ? 'text-gray-400'
    : Number(delta) > 0 ? 'text-green-600'
      : Number(delta) < 0 ? 'text-red-600'
        : 'text-gray-500'
  const side = hasDelta
    ? `${Number(delta) > 0 ? '+' : ''}${Number(delta).toFixed(2)}%`
    : (note || null)

  return (
    <div className="flex items-baseline justify-between gap-3 py-1.5 border-b border-gray-100 last:border-0">
      <span className="text-xs text-gray-500 shrink-0">{label}</span>
      <div className="min-w-0 text-right">
        <span className="text-sm font-semibold text-gray-900">{value}</span>
        {side && <span className={`ml-2 text-xs ${tone}`}>{side}</span>}
      </div>
    </div>
  )
}

MacroRow.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.node,
  delta: PropTypes.number,
  note: PropTypes.string,
}

function tileValue(tile) {
  if (!tile || tile.value == null || Number.isNaN(Number(tile.value))) return '—'
  const n = Number(tile.value)
  return tile.unit === '%' ? `${n.toFixed(2)}%` : n.toLocaleString('en-US', { maximumFractionDigits: 2 })
}

export default function ChartsPage({
  predictionDate = null,
  week = null,
  technical = null,
  macro = null,
  finalPrediction = null,
}) {
  const [symbol, setSymbol] = useState(instruments[0].symbol)
  const [rangeId, setRangeId] = useState('3M')
  const [data, setData] = useState(null)
  const [compare, setCompare] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [showVolume, setShowVolume] = useState(true)
  const [relative, setRelative] = useState(false)
  const [sectorImg, setSectorImg] = useState(null)
  const [actuals, setActuals] = useState({})

  const days = RANGES.find(r => r.id === rangeId)?.days ?? 66
  const endDate = predictionDate || undefined
  const stem = weekStem(week)

  const tech = COMPARE.includes(symbol) ? technicalContext(technical, symbol) : null
  const mac = macroContext(macro)
  const pred = predictedRangeForSymbol(symbol, { finalPrediction })
  const windowPct = periodChangePct(data?.candles)
  const weekActual = actuals[symbol]?.move_pct
  const hit = rangeHit(pred, weekActual)
  const decimals = data?.decimals ?? 2
  const up = (data?.stats?.change ?? 0) >= 0
  const hasMacro = Boolean(mac?.yield10y || mac?.dxy || mac?.wti || mac?.fedRate || mac?.bias)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    const toFetch = COMPARE.includes(symbol) ? COMPARE : [...COMPARE, symbol]

    Promise.all(
      toFetch.map(sym =>
        getMarketHistory(sym, { days, endDate })
          .then(d => [sym, d])
          .catch(err => {
            if (sym === symbol) throw err
            return [sym, null]
          }),
      ),
    )
      .then(rows => {
        if (!active) return
        const map = Object.fromEntries(rows)
        setCompare(Object.fromEntries(COMPARE.map(s => [s, map[s] ?? null])))
        const d = map[symbol]
        if (!d) throw new Error(`Could not load ${symbol}`)
        setData(d)
      })
      .catch(err => {
        if (active) {
          setError(err?.message ? `Could not load ${symbol}: ${err.message}` : `Could not load ${symbol}`)
        }
      })
      .finally(() => { if (active) setLoading(false) })

    return () => { active = false }
  }, [symbol, days, endDate, reloadKey])

  useEffect(() => {
    if (!stem) {
      setSectorImg(null)
      setActuals({})
      return
    }
    let active = true
    getEvidenceImages(stem)
      .then(list => { if (active) setSectorImg(list.find(i => /sectors/i.test(i.name)) || null) })
      .catch(() => { if (active) setSectorImg(null) })
    getActuals(stem)
      .then(res => { if (active) setActuals(res.assets || {}) })
      .catch(() => { if (active) setActuals({}) })
    return () => { active = false }
  }, [stem])

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Market Charts</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Candles + 8/21 EMA
            {endDate ? ` · as of ${endDate}` : ''}
            {week ? ` · ${week}` : ''}
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {RANGES.map(r => (
            <button key={r.id} type="button" onClick={() => setRangeId(r.id)} className={chipClass(rangeId === r.id)}>
              {r.label}
            </button>
          ))}
          <button type="button" onClick={() => setShowVolume(v => !v)} className={chipClass(showVolume)}>
            Volume
          </button>
          <button type="button" onClick={() => setRelative(v => !v)} className={chipClass(relative)}>
            Relative
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {instruments.map(inst => (
          <button
            key={inst.symbol}
            type="button"
            onClick={() => setSymbol(inst.symbol)}
            className={`px-3 py-1.5 text-sm font-medium rounded-md border ${
              symbol === inst.symbol
                ? 'bg-gray-900 border-gray-900 text-white'
                : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {inst.symbol}
          </button>
        ))}
      </div>

      <ErrorBanner message={error} onRetry={() => setReloadKey(k => k + 1)} onDismiss={() => setError(null)} />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {COMPARE.map(sym => {
          const d = compare[sym]
          const pct = periodChangePct(d?.candles)
          const positive = (pct ?? 0) >= 0
          return (
            <button
              key={sym}
              type="button"
              onClick={() => setSymbol(sym)}
              className={`text-left bg-white border rounded-md shadow-sm px-3 py-2.5 ${
                symbol === sym ? 'border-gray-900' : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-gray-900">{sym}</span>
                <span className={`text-sm font-semibold ${positive ? 'text-green-600' : 'text-red-600'}`}>
                  {fmtPct(pct)}
                </span>
              </div>
              <p className="text-[11px] text-gray-400 mt-0.5 truncate">
                {d?.stats ? `Last ${fmt(d.stats.last, d.decimals ?? 0)}` : '—'}
                {' · '}
                {rangeId} window
              </p>
            </button>
          )
        })}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 space-y-3">
          <div className="bg-white border border-gray-200 rounded-lg shadow-md p-4 md:p-5">
            {data?.stats && (
              <div className="flex flex-wrap items-end justify-between gap-3 mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-gray-900">{data.name}</h3>
                    <span className="text-xs text-gray-400">{data.symbol} · {data.yahoo}</span>
                  </div>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-2xl font-semibold text-gray-900">
                      {relative ? fmtPct(windowPct) : fmt(data.stats.last, decimals)}
                    </span>
                    {!relative && (
                      <span className={`flex items-center gap-0.5 text-sm font-medium ${up ? 'text-green-600' : 'text-red-600'}`}>
                        {up ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        {up ? '+' : ''}{fmt(data.stats.change, decimals)} ({up ? '+' : ''}{data.stats.changePct}%)
                      </span>
                    )}
                    {relative && <span className="text-xs text-gray-500">{rangeId} window</span>}
                  </div>
                </div>
                {!relative && (
                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block w-3 h-0.5 bg-blue-600" /> 8 EMA
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block w-3 h-0.5 bg-amber-500" /> 21 EMA
                    </span>
                  </div>
                )}
              </div>
            )}

            {loading || !data ? (
              <div className="h-[440px] flex items-center justify-center text-sm text-gray-400">
                Loading chart…
              </div>
            ) : (
              <PriceChart data={data} showVolume={showVolume} relative={relative} />
            )}
          </div>

          {tech && (
            <div className="bg-white border border-gray-200 rounded-md shadow-sm px-3 py-2.5 text-xs text-gray-700 flex flex-wrap gap-x-4 gap-y-1">
              <span className="font-medium text-gray-900">Technical</span>
              {tech.lastClose != null && <span>Last {fmt(tech.lastClose, decimals)}</span>}
              {tech.bias && <span>Bias {tech.bias}</span>}
              {tech.support != null && <span>Support {fmt(tech.support, decimals)}</span>}
              {tech.resistance != null && <span>Resistance {fmt(tech.resistance, decimals)}</span>}
            </div>
          )}

          {COMPARE.includes(symbol) && (pred || weekActual != null) && (
            <div className="bg-violet-50 border border-violet-100 rounded-md px-3 py-2.5 text-xs text-violet-900 flex flex-wrap gap-x-4 gap-y-1">
              <span className="font-medium">Prediction vs week{stem ? ` ${stem}` : ''}</span>
              {pred ? (
                <span>Pred {fmtPct(pred.low)} to {fmtPct(pred.high)} ({pred.source})</span>
              ) : (
                <span>No Final Prediction range for {symbol}</span>
              )}
              <span>
                {weekActual != null ? `Actual ${fmtPct(weekActual)}` : 'Actual — no weekly actuals yet'}
              </span>
              {pred?.direction && <span>Call {pred.direction}</span>}
              {hit != null && <span>{hit ? 'Range hit' : 'Missed range'}</span>}
            </div>
          )}

          {data?.stats && !relative && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <StatBox label="Period High" value={fmt(data.stats.periodHigh, decimals)} />
              <StatBox label="Period Low" value={fmt(data.stats.periodLow, decimals)} />
              <StatBox label="8 EMA" value={fmt(data.stats.ema8, decimals)} />
              <StatBox label="21 EMA" value={fmt(data.stats.ema21, decimals)} />
              <StatBox label="EMA Zone" value={data.stats.aboveEmas ? 'Bullish' : 'Caution'} />
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-lg shadow-md p-4">
            <div className="mb-3">
              <h3 className="text-sm font-medium text-gray-900">Macro snapshot</h3>
              <p className="text-xs text-gray-500 mt-0.5">
                From Macro agent{week ? ` · ${week}` : ''}
              </p>
            </div>
            {!hasMacro ? (
              <p className="text-sm text-gray-400">Run Macro or open a week with macro output.</p>
            ) : (
              <div>
                {mac.bias && <MacroRow label="Bias" value={mac.bias} />}
                {mac.yield10y?.value != null && (
                  <MacroRow
                    label="10Y"
                    value={tileValue(mac.yield10y)}
                    delta={mac.yield10y.change}
                    note={mac.yield10y.direction}
                  />
                )}
                {mac.dxy?.value != null && (
                  <MacroRow label="DXY" value={tileValue(mac.dxy)} delta={mac.dxy.change} note={mac.dxy.direction} />
                )}
                {mac.wti?.value != null && (
                  <MacroRow label="WTI" value={tileValue(mac.wti)} delta={mac.wti.change} note={mac.wti.direction} />
                )}
                {mac.fedRate && <MacroRow label="Fed" value={mac.fedRate} />}
              </div>
            )}
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-md overflow-hidden">
            <div className="px-4 pt-4 pb-2">
              <h3 className="text-sm font-medium text-gray-900">Sector heatmap</h3>
              <p className="text-xs text-gray-500 mt-0.5">
                Finviz 5D sectors{week ? ` · ${week}` : ''}
              </p>
            </div>
            {sectorImg ? (
              <a href={sectorImg.url} target="_blank" rel="noreferrer" className="block bg-gray-50">
                <img
                  src={sectorImg.url}
                  alt={sectorImg.label}
                  className="w-full h-auto max-h-[320px] object-contain"
                  loading="lazy"
                />
              </a>
            ) : (
              <p className="px-4 pb-4 text-sm text-gray-400">No sector image for this week yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

ChartsPage.propTypes = {
  predictionDate: PropTypes.string,
  week: PropTypes.string,
  technical: PropTypes.object,
  macro: PropTypes.object,
  finalPrediction: PropTypes.object,
}
