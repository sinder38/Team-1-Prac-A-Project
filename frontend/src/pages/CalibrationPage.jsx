/**
 * Locked predictions vs completed actuals (Delta calibration).
 */
import { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { RefreshCw } from 'lucide-react'

import { getCalibrationScores } from '../api'
import { ErrorBanner } from '../components/common'
import { AGENT_BAR_COLORS, AGENTS } from '../lib/constants'
import { formatDateTime } from '../lib/date'
import { defaultCalibration } from '../lib/defaults'

function pct(n) {
  if (n == null || Number.isNaN(Number(n))) return '—'
  return `${n}%`
}

function weekLabel(week) {
  return week ? String(week).replace(/^v/i, '') : '—'
}

export default function CalibrationPage({ pipeline }) {
  const [scores, setScores] = useState(defaultCalibration)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  function load() {
    setBusy(true)
    setError(null)
    getCalibrationScores()
      .then(setScores)
      .catch(err => setError(err?.message || 'Could not load calibration'))
      .finally(() => setBusy(false))
  }

  useEffect(() => {
    load()
  }, [pipeline.lastRun])

  const trend = Array.isArray(scores.weeklyTrend) ? scores.weeklyTrend : []
  const weights = Object.entries(scores.suggestedWeights || {})

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6 space-y-5">
      <div className="flex justify-between items-start gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Calibration</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Locked Final Predictions vs completed actuals. Only matched weeks count.
          </p>
        </div>
        <button
          type="button"
          onClick={load}
          disabled={busy}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 rounded-xl hover:bg-gray-50 shrink-0"
        >
          <RefreshCw className={`w-4 h-4 ${busy ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <ErrorBanner message={error} onRetry={load} onDismiss={() => setError(null)} />

      <section className="bg-white border border-gray-200 rounded-xl shadow-md p-5">
        <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
          Latest scored week
        </p>
        {scores.latestWeek ? (
          <>
            <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <h3 className="text-2xl font-semibold text-gray-900">
                {weekLabel(scores.latestWeek)}
              </h3>
              <span className="text-sm text-gray-500">
                Updated {formatDateTime(scores.lastCalculated)}
              </span>
            </div>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Tile
                label="Direction"
                value={pct(scores.latestDirectionAccuracy)}
                detail="Up / down / flat that week"
              />
              <Tile
                label="Range"
                value={pct(scores.latestRangeAccuracy)}
                detail="Actual inside predicted band"
              />
              <Tile
                label="Sectors"
                value={`${scores.sectorCoverage} / ${scores.sectorTotal}`}
                detail="Rows on the latest score sheet"
              />
            </div>
          </>
        ) : (
          <p className="mt-3 text-sm text-gray-500">
            Nothing scored yet — lock a prediction, wait for actuals, run Delta.
          </p>
        )}
      </section>

      <section>
        <div className="mb-3">
          <h3 className="text-sm font-medium text-gray-900">Cumulative</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {trend.length
              ? `${trend.length} week${trend.length === 1 ? '' : 's'} averaged — early 0% weeks drag this down`
              : 'No history yet'}
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Tile
            label="Overall"
            value={pct(scores.totalAccuracy)}
            detail="Direction + range hits"
            emphasize
          />
          <Tile
            label="Direction"
            value={pct(scores.currentAccuracy)}
            detail="All scored weeks"
          />
          <Tile
            label="Range"
            value={pct(scores.rangeAccuracy)}
            detail="All scored weeks"
          />
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-xl shadow-md overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="text-sm font-medium text-gray-900">Week by week</h3>
        </div>
        {trend.length === 0 ? (
          <p className="px-5 py-8 text-sm text-gray-500 text-center">No scored weeks yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-left">
              <thead className="bg-gray-50 text-xs uppercase tracking-wide text-gray-500">
                <tr>
                  <th className="px-5 py-2.5 font-medium">Week</th>
                  <th className="px-5 py-2.5 font-medium">Direction</th>
                  <th className="px-5 py-2.5 font-medium">Range</th>
                  <th className="px-5 py-2.5 font-medium min-w-[8rem]" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {trend.map(item => (
                  <tr key={item.week} className="text-gray-800">
                    <td className="px-5 py-3 font-medium whitespace-nowrap">
                      {weekLabel(item.week)}
                    </td>
                    <td className="px-5 py-3 tabular-nums">{pct(item.directionAccuracy)}</td>
                    <td className="px-5 py-3 tabular-nums">{pct(item.rangeAccuracy)}</td>
                    <td className="px-5 py-3">
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden max-w-[12rem]">
                        <div
                          className="h-full bg-gray-700 rounded-full"
                          style={{ width: `${Math.min(100, item.directionAccuracy || 0)}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="bg-white border border-gray-200 rounded-xl shadow-md p-5">
          <h3 className="text-sm font-medium text-gray-900">Suggested weights</h3>
          <p className="text-xs text-gray-500 mt-0.5 mb-4">Trial tweaks from Delta — review before use</p>
          {weights.length === 0 ? (
            <p className="text-sm text-gray-500">None yet</p>
          ) : (
            <div className="space-y-3">
              {weights.map(([id, percentage]) => (
                <div key={id}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700">{AGENTS[id]?.label || id}</span>
                    <span className="font-semibold tabular-nums">{percentage}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${AGENT_BAR_COLORS[id] || 'bg-gray-500'}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="bg-white border border-gray-200 rounded-xl shadow-md p-5">
          <h3 className="text-sm font-medium text-gray-900">Next sprint</h3>
          <p className="text-xs text-gray-500 mt-0.5 mb-3">From the latest Delta report</p>
          <p className="text-sm text-gray-700 leading-relaxed">
            {scores.prescription || 'No prescription yet.'}
          </p>
        </section>
      </div>
    </div>
  )
}

function Tile({ label, value, detail, emphasize = false }) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        emphasize
          ? 'bg-white border-gray-900 shadow-md ring-1 ring-gray-900/10'
          : 'bg-gray-50/80 border-gray-100'
      }`}
    >
      <p className="text-[11px] font-medium uppercase tracking-wide text-gray-400">{label}</p>
      <p className={`font-semibold mt-1 tabular-nums text-gray-900 ${emphasize ? 'text-3xl' : 'text-2xl'}`}>
        {value}
      </p>
      <p className="text-xs text-gray-500 mt-1">{detail}</p>
    </div>
  )
}

Tile.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  detail: PropTypes.string.isRequired,
  emphasize: PropTypes.bool,
}

CalibrationPage.propTypes = {
  pipeline: PropTypes.shape({
    lastRun: PropTypes.string,
  }).isRequired,
}
