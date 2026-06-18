/**
 * Shows how accurate our predictions are over time.
 * TODO (backend task): load live scores via getCalibrationScores() → GET /api/calibration/accuracy-tracker
 */
import { useState, useEffect } from 'react'
import { BarChart3, RefreshCw, Target, TrendingUp, TrendingDown } from 'lucide-react'
import { getCalibrationScores } from '../api'
import { defaultCalibration } from '../lib/defaults'
import { AGENTS, AGENT_BAR_COLORS } from '../lib/constants'
import { formatDateTime } from '../lib/date'

export default function CalibrationPage({ pipeline }) {
  const [scores, setScores] = useState(defaultCalibration)
  const [busy, setBusy] = useState(false)

  function load() {
    setBusy(true)
    getCalibrationScores()
      .then(setScores)
      .catch(() => {})
      .finally(() => setBusy(false))
  }

  useEffect(() => { load() }, [pipeline.lastRun])

  const delta = scores.weeklyTrend.length >= 2
    ? scores.currentAccuracy - scores.weeklyTrend[0]
    : 0
  const progress = Math.min(100, (scores.currentAccuracy / scores.targetAccuracy) * 100)
  const maxBar = Math.max(...scores.weeklyTrend, scores.targetAccuracy, 1)

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6 space-y-4">
      <div className="flex justify-between items-start gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Calibration Tracker</h2>
          <p className="text-sm text-gray-500 mt-0.5">Agent alignment vs LLM consensus</p>
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 bg-white border border-gray-200 rounded-md p-5">
          <div className="flex justify-between mb-4">
            <div>
              <p className="text-xs text-gray-500 uppercase">Overall Accuracy</p>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-4xl font-semibold">{scores.currentAccuracy}%</span>
                <span className={`flex items-center gap-0.5 text-sm ${delta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {delta >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  {delta >= 0 ? '+' : ''}{delta}%
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Target</p>
              <p className="text-lg font-semibold flex items-center gap-1 justify-end">
                <Target className="w-4 h-4 text-gray-400" />
                {scores.targetAccuracy}%
              </p>
            </div>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-gray-700 rounded-full" style={{ width: `${progress}%` }} />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Updated {formatDateTime(scores.lastCalculated)}
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-md p-5">
          <p className="text-xs text-gray-500 uppercase mb-3">Latest Run</p>
          <p className="text-3xl font-semibold">
            {pipeline.accuracy ? `${pipeline.accuracy}%` : '—'}
          </p>
          {pipeline.lastRun && (
            <p className="text-xs text-gray-500 mt-2">
              {new Date(pipeline.lastRun).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-md p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4 text-gray-500" />
            <p className="text-sm font-medium">Weekly Trend</p>
          </div>
          <div className="flex items-end gap-2 h-40">
            {scores.weeklyTrend.map((v, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-xs font-medium">{v}%</span>
                <div className="w-full bg-gray-200 rounded-t-md relative" style={{ height: 120 }}>
                  <div
                    className={`absolute bottom-0 w-full rounded-t-md ${i === scores.weeklyTrend.length - 1 ? 'bg-gray-800' : 'bg-gray-400'}`}
                    style={{ height: `${(v / maxBar) * 100}%` }}
                  />
                </div>
              </div>
            ))}
            <div className="flex-1 flex flex-col items-center gap-1">
              <span className="text-xs font-medium text-green-700">{scores.targetAccuracy}%</span>
              <div className="w-full bg-gray-200 rounded-t-md relative" style={{ height: 120 }}>
                <div
                  className="absolute bottom-0 w-full bg-green-500 rounded-t-md opacity-60"
                  style={{ height: `${(scores.targetAccuracy / maxBar) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-400">Target</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-md p-5">
          <p className="text-sm font-medium mb-4">Per Agent</p>
          <div className="space-y-4">
            {Object.entries(scores.agentAccuracies).map(([id, pct]) => (
              <div key={id}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{AGENTS[id]?.label || id}</span>
                  <span className="font-semibold">{pct}%</span>
                </div>
                <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${AGENT_BAR_COLORS[id] || 'bg-gray-500'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
