import { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { BarChart3, RefreshCw, Target } from 'lucide-react'

import { getCalibrationScores } from '../api'
import { ErrorBanner } from '../components/common'
import { AGENT_BAR_COLORS, AGENTS } from '../lib/constants'
import { formatDateTime } from '../lib/date'
import { defaultCalibration } from '../lib/defaults'

export default function CalibrationPage({ pipeline }) {
  const [scores, setScores] = useState(defaultCalibration)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  function load() {
    setBusy(true)
    setError(null)
    getCalibrationScores()
      .then(setScores)
      .catch(err =>
        setError(err?.message ? `Could not load calibration: ${err.message}` : 'Could not load calibration'),
      )
      .finally(() => setBusy(false))
  }

  useEffect(() => { load() }, [pipeline.lastRun])

  const trend = Array.isArray(scores.weeklyTrend) ? scores.weeklyTrend : []
  const suggestedWeights = scores.suggestedWeights || {}
  const maxBar = Math.max(...trend.map(item => item.directionAccuracy || 0), 100)

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6 space-y-4">
      <div className="flex justify-between items-start gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Calibration Tracker</h2>
          <p className="text-sm text-gray-500 mt-0.5">Locked predictions compared with completed actuals</p>
        </div>
        <button
          onClick={load}
          disabled={busy}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 rounded-md hover:bg-gray-50"
        >
          <RefreshCw className={`w-4 h-4 ${busy ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <ErrorBanner message={error} onRetry={load} onDismiss={() => setError(null)} />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          label="Cumulative Direction Accuracy"
          value={`${scores.currentAccuracy}%`}
          detail={`Latest: ${scores.latestDirectionAccuracy}%`}
        />
        <MetricCard
          label="Cumulative Range Accuracy"
          value={`${scores.rangeAccuracy}%`}
          detail={`Latest: ${scores.latestRangeAccuracy}%`}
        />
        <MetricCard
          label="Sector Coverage"
          value={`${scores.sectorCoverage} / ${scores.sectorTotal}`}
          detail={scores.latestWeek || 'No scored week'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-md shadow-md p-5">
          <div className="flex items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-gray-500" />
              <p className="text-sm font-medium">Weekly Direction Accuracy</p>
            </div>
            <p className="text-xs text-gray-400">Updated {formatDateTime(scores.lastCalculated)}</p>
          </div>
          <div className="flex items-end gap-3 h-44">
            {trend.map(item => (
              <div key={item.week} className="flex-1 min-w-0 flex flex-col items-center gap-1">
                <span className="text-xs font-medium">{item.directionAccuracy}%</span>
                <div className="w-full bg-gray-100 rounded-t-md relative" style={{ height: 120 }}>
                  <div
                    className="absolute bottom-0 w-full bg-gray-700 rounded-t-md"
                    style={{ height: `${(item.directionAccuracy / maxBar) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 truncate w-full text-center">{item.week}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-md shadow-md p-5">
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-4 h-4 text-gray-500" />
            <p className="text-sm font-medium">Suggested Weights</p>
          </div>
          <div className="space-y-4">
            {Object.entries(suggestedWeights).map(([id, percentage]) => (
              <div key={id}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{AGENTS[id]?.label || id}</span>
                  <span className="font-semibold">{percentage}%</span>
                </div>
                <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${AGENT_BAR_COLORS[id] || 'bg-gray-500'}`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {scores.prescription && (
        <section className="border-t border-gray-200 pt-4">
          <h3 className="text-sm font-medium text-gray-900">Next Sprint Prescription</h3>
          <p className="text-sm text-gray-600 mt-2 leading-6">{scores.prescription}</p>
        </section>
      )}
    </div>
  )
}

function MetricCard({ label, value, detail }) {
  return (
    <div className="bg-white border border-gray-200 rounded-md shadow-md p-5">
      <p className="text-xs text-gray-500 uppercase">{label}</p>
      <p className="text-3xl font-semibold mt-2">{value}</p>
      <p className="text-xs text-gray-500 mt-2">{detail}</p>
    </div>
  )
}

MetricCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  detail: PropTypes.string.isRequired,
}

CalibrationPage.propTypes = {
  pipeline: PropTypes.shape({
    lastRun: PropTypes.string,
  }).isRequired,
}
