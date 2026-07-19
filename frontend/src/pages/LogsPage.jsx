/**
 * Shows pipeline run info and per-stage status.
 */
import PropTypes from 'prop-types'
import { CheckCircle2, AlertCircle, Clock, Play } from 'lucide-react'
import { formatDateTime } from '../lib/date'

function StageIcon({ status }) {
  if (status === 'success') return <CheckCircle2 className="w-4 h-4 text-green-600" />
  if (status === 'error') return <AlertCircle className="w-4 h-4 text-red-600" />
  if (status === 'in-progress') return <Clock className="w-4 h-4 text-gray-600 animate-spin" />
  return <Clock className="w-4 h-4 text-gray-300" />
}

StageIcon.propTypes = {
  status: PropTypes.string,
}

export default function LogsPage({ pipeline, controls, week, predictionDate }) {
  const { isRunning, allDone, aiStages, doneCount, runNext } = controls

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Execution Logs</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            {week || pipeline.week || '—'}
            {predictionDate ? ` · ${predictionDate}` : ''}
          </p>
        </div>
        <div className="flex gap-2">
          {doneCount < aiStages ? (
            <button
              onClick={runNext}
              disabled={isRunning}
              className={`flex items-center gap-2 px-3 py-2 text-sm rounded-md font-medium ${
                isRunning
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-900 text-white hover:bg-gray-800'
              }`}
            >
              <Play className="w-4 h-4" />
              {isRunning ? 'Running…' : `Run stage ${doneCount + 1}`}
            </button>
          ) : (
            <span className="flex items-center gap-2 px-3 py-2 text-sm text-gray-500">
              {allDone ? 'Run complete' : 'AI stages done — submit Human Score'}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          ['Run ID', pipeline.id || controls.runId || '—'],
          ['Status', pipeline.isRunning ? 'Running' : pipeline.lastRun ? 'Completed' : 'Idle'],
          ['Last Run', formatDateTime(pipeline.lastRun)],
          ['Accuracy', pipeline.accuracy ? `${pipeline.accuracy}%` : '—'],
        ].map(([label, value]) => (
          <div key={label} className="bg-white border border-gray-200 rounded-md shadow-md p-4">
            <p className="text-xs text-gray-500 uppercase">{label}</p>
            <p className="text-sm font-medium text-gray-900 mt-1 truncate">{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white border border-gray-200 rounded-md shadow-md overflow-hidden">
        <div className="px-4 py-3">
          <p className="text-xs text-gray-500 uppercase mb-3">Stages</p>
          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-2">
            {pipeline.stages.map((stage, i) => (
              <div
                key={stage.id}
                className={`px-3 py-2 rounded-md border text-sm ${
                  stage.status === 'success' ? 'bg-green-50 border-green-200'
                  : stage.status === 'error' ? 'bg-red-50 border-red-200'
                  : stage.status === 'in-progress' ? 'bg-gray-50 border-gray-400'
                  : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">{i + 1}</span>
                  <StageIcon status={stage.status} />
                  <span className="text-xs font-medium truncate">{stage.name}</span>
                </div>
                {stage.timestamp && (
                  <p className="text-xs text-gray-400 mt-1">{formatDateTime(stage.timestamp)}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

LogsPage.propTypes = {
  pipeline: PropTypes.shape({
    id: PropTypes.string,
    isRunning: PropTypes.bool,
    lastRun: PropTypes.string,
    accuracy: PropTypes.number,
    stages: PropTypes.array.isRequired,
    week: PropTypes.string,
  }).isRequired,
  controls: PropTypes.object.isRequired,
  week: PropTypes.string,
  predictionDate: PropTypes.string,
}
