/**
 * Price charts for the tracked instruments (SPX, NDX, IWM, Gold, Oil, DXY).
 * Candlestick + 8/21 EMA, styled like ProRealTime / yfinance.
 * TODO (backend task): data comes from example generator — swap getMarketHistory
 * to the real yfinance-backed endpoint (see src/api/market.js).
 */
import { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { PriceChart } from '../components/charts'
import { ErrorBanner } from '../components/common'
import { getInstruments, getMarketHistory } from '../api'

const instruments = getInstruments()

function formatNumber(value, decimals) {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
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

export default function ChartsPage() {
  const [symbol, setSymbol] = useState(instruments[0].symbol)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    getMarketHistory(symbol)
      .then(d => {
        if (active) setData(d)
      })
      .catch(err => {
        if (active) setError(err?.message ? `Could not load ${symbol}: ${err.message}` : `Could not load ${symbol}`)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [symbol, reloadKey])

  const decimals = data?.decimals ?? 2
  const up = (data?.stats?.change ?? 0) >= 0

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6 space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Market Charts</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Daily candlesticks with 8 &amp; 21 EMA — SPX, NDX, IWM and macro assets
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {instruments.map(inst => (
          <button
            key={inst.symbol}
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
                  {formatNumber(data.stats.last, decimals)}
                </span>
                <span className={`flex items-center gap-0.5 text-sm font-medium ${up ? 'text-green-600' : 'text-red-600'}`}>
                  {up ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  {up ? '+' : ''}{formatNumber(data.stats.change, decimals)} ({up ? '+' : ''}{data.stats.changePct}%)
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-gray-600">
                <span className="inline-block w-3 h-0.5 bg-blue-600" /> 8 EMA
              </span>
              <span className="flex items-center gap-1.5 text-gray-600">
                <span className="inline-block w-3 h-0.5 bg-amber-500" /> 21 EMA
              </span>
            </div>
          </div>
        )}

        {loading || !data ? (
          <div className="h-[440px] flex items-center justify-center text-sm text-gray-400">
            Loading chart…
          </div>
        ) : (
          <PriceChart data={data} />
        )}
      </div>

      {data?.stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatBox label="Period High" value={formatNumber(data.stats.periodHigh, decimals)} />
          <StatBox label="Period Low" value={formatNumber(data.stats.periodLow, decimals)} />
          <StatBox label="8 EMA" value={formatNumber(data.stats.ema8, decimals)} />
          <StatBox label="21 EMA" value={formatNumber(data.stats.ema21, decimals)} />
          <StatBox
            label="EMA Zone"
            value={data.stats.aboveEmas ? 'Bullish' : 'Caution'}
          />
        </div>
      )}
    </div>
  )
}
