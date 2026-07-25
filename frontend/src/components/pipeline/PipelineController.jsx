/**
 * Manual pipeline control — the human runs each stage one at a time.
 * Stages 1-4 have a Run button; stage 5 (Human Score) is filled in on the Dashboard.
 */
import PropTypes from 'prop-types'
import {
  Play,
  CheckCircle2,
  AlertCircle,
  Clock,
  Lock,
  RotateCcw,
  ScrollText,
  BarChart3,
  FileDown,
} from 'lucide-react'
import WeekPicker from './WeekPicker'
import { ErrorBanner } from '../common'

function StatusBadge({ label, tone }) {
  const tones = {
    idle: 'bg-gray-50 text-gray-500',
    running: 'bg-blue-50 text-blue-700',
    done: 'bg-green-50 text-green-700',
    error: 'bg-red-50 text-red-700',
  }
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${tones[tone]}`}>{label}</span>
}

function StageIcon({ status, locked }) {
  if (status === 'success') return <CheckCircle2 className="w-5 h-5 text-green-600" />
  if (status === 'error') return <AlertCircle className="w-5 h-5 text-red-600" />
  if (status === 'in-progress') return <Clock className="w-5 h-5 text-blue-600 animate-spin" />
  if (locked) return <Lock className="w-4 h-4 text-gray-300" />
  return <span className="text-xs font-medium text-gray-400">—</span>
}

const LLM_STAGE_INDEX = 2

function ModelSelector({ availableModels, selectedModels, toggleModel, disabled }) {
  if (!availableModels.length) return null
  return (
    <div className="mt-2 pl-9 flex flex-wrap gap-x-4 gap-y-1.5">
      {availableModels.map(({ key, name }) => (
        <label
          key={key}
          className={`flex items-center gap-1.5 text-xs ${disabled ? 'text-gray-400' : 'text-gray-600'}`}
        >
          <input
            type="checkbox"
            checked={selectedModels.includes(key)}
            onChange={() => toggleModel(key)}
            disabled={disabled}
            className="rounded border-gray-300"
          />
          {name}
        </label>
      ))}
    </div>
  )
}

ModelSelector.propTypes = {
  availableModels: PropTypes.array.isRequired,
  selectedModels: PropTypes.array.isRequired,
  toggleModel: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
}

export default function PipelineController({ pipeline, controls, weekPicker, onNavigate }) {
  const {
    doneCount,
    isRunning,
    allDone,
    aiStages,
    error,
    clearError,
    runStage,
    runNext,
    resetRun,
    availableModels = [],
    selectedModels = [],
    toggleModel,
    exportArtifacts,
    exporting = false,
    exportStatus,
    canExport = false,
  } = controls
  const stages = pipeline.stages

  const statusLabel = isRunning ? 'Running' : allDone ? 'Complete' : doneCount > 0 ? 'In progress' : 'Idle'
  const statusTone = isRunning ? 'running' : allDone ? 'done' : 'idle'

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-md mx-4 mt-4 px-4 py-4 md:px-6">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-gray-900">Pipeline</h2>
              <StatusBadge label={statusLabel} tone={statusTone} />
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              {doneCount}/{pipeline.stages.length} stages
              {pipeline.accuracy ? ` · ${pipeline.accuracy}% accuracy` : ''} · run one step at a time
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {exportArtifacts && (
              <button
                onClick={exportArtifacts}
                disabled={!canExport}
                title="Write the stored data for this week to data/<agent>/*.md"
                className="flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:text-gray-300 disabled:hover:bg-white"
              >
                <FileDown className="w-4 h-4" />
                {exporting ? 'Exporting…' : 'Export .md'}
              </button>
            )}
            <button
              onClick={resetRun}
              disabled={isRunning || doneCount === 0}
              className="flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:text-gray-300 disabled:hover:bg-white"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
            {doneCount < aiStages && (() => {
              const blockedByModels = doneCount === LLM_STAGE_INDEX && selectedModels.length === 0
              return (
                <button
                  onClick={runNext}
                  disabled={isRunning || blockedByModels}
                  title={blockedByModels ? 'Select at least one LLM model to run this stage' : undefined}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium ${
                    isRunning || blockedByModels
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-900 text-white hover:bg-gray-800'
                  }`}
                >
                  <Play className="w-4 h-4" />
                  {isRunning ? 'Running…' : `Run stage ${doneCount + 1}`}
                </button>
              )
            })()}
          </div>
        </div>

        <WeekPicker {...weekPicker} disabled={isRunning} />
      </div>

      {error && (
        <div className="mt-4">
          <ErrorBanner message={error} onDismiss={clearError} />
        </div>
      )}

      {exportStatus && (
        <div
          className={`mt-3 text-xs rounded-md px-3 py-2 ${
            exportStatus.tone === 'success'
              ? 'bg-green-50 text-green-700 border border-green-100'
              : 'bg-red-50 text-red-700 border border-red-100'
          }`}
        >
          <p className="font-medium">{exportStatus.message}</p>
          {exportStatus.files?.length > 0 && (
            <ul className="mt-1 space-y-0.5 font-mono text-[11px] text-green-800/80">
              {exportStatus.files.map(f => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="mt-5 space-y-2">
        {stages.map((stage, i) => {
          const isNext = i === doneCount && !isRunning && i < aiStages
          const isHumanStage = i === aiStages
          const locked = i > doneCount
          const tone =
            stage.status === 'success' ? 'done'
            : stage.status === 'in-progress' ? 'running'
            : stage.status === 'error' ? 'error'
            : 'idle'
          const label =
            stage.status === 'success' ? 'Done'
            : stage.status === 'in-progress' ? 'Running'
            : locked ? 'Locked'
            : 'Pending'

          return (
            <div
              key={stage.id}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md border ${
                stage.status === 'in-progress' ? 'border-blue-200 bg-blue-50/40'
                : stage.status === 'success' ? 'border-green-100 bg-green-50/30'
                : 'border-gray-100 bg-white'
              }`}
            >
              <div className="w-6 flex justify-center shrink-0">
                <StageIcon status={stage.status} locked={locked} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">
                    {i + 1}. {stage.name}
                  </span>
                  <StatusBadge label={label} tone={tone} />
                </div>
                <p className="text-xs text-gray-500 mt-0.5 truncate">{stage.description}</p>
                {i === LLM_STAGE_INDEX && (
                  <ModelSelector
                    availableModels={availableModels}
                    selectedModels={selectedModels}
                    toggleModel={toggleModel}
                    disabled={locked || isRunning || stage.status === 'success'}
                  />
                )}
              </div>

              <div className="shrink-0">
                {stage.status === 'success' ? (
                  <span className="text-xs text-green-600 font-medium">✓</span>
                ) : isHumanStage ? null : (
                  <button
                    onClick={() => runStage(i)}
                    disabled={!isNext || (i === LLM_STAGE_INDEX && selectedModels.length === 0)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md ${
                      isNext && !(i === LLM_STAGE_INDEX && selectedModels.length === 0)
                        ? 'bg-gray-900 text-white hover:bg-gray-800'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {stage.status === 'in-progress' ? 'Running…' : 'Run'}
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {onNavigate && (
        <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
          <button
            onClick={() => onNavigate('logs')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50"
          >
            <ScrollText className="w-3.5 h-3.5" />
            View Logs
          </button>
          <button
            onClick={() => onNavigate('calibration')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Calibration
          </button>
        </div>
      )}
    </div>
  )
}

StatusBadge.propTypes = {
  label: PropTypes.string.isRequired,
  tone: PropTypes.oneOf(['idle', 'running', 'done', 'error']).isRequired,
}

StageIcon.propTypes = {
  status: PropTypes.string,
  locked: PropTypes.bool,
}

PipelineController.propTypes = {
  pipeline: PropTypes.shape({
    stages: PropTypes.array.isRequired,
    accuracy: PropTypes.number,
  }).isRequired,
  controls: PropTypes.shape({
    doneCount: PropTypes.number,
    isRunning: PropTypes.bool,
    allDone: PropTypes.bool,
    aiStages: PropTypes.number,
    error: PropTypes.string,
    clearError: PropTypes.func,
    runStage: PropTypes.func,
    runNext: PropTypes.func,
    resetRun: PropTypes.func,
    availableModels: PropTypes.array,
    selectedModels: PropTypes.array,
    toggleModel: PropTypes.func,
    exportArtifacts: PropTypes.func,
    exporting: PropTypes.bool,
    exportStatus: PropTypes.shape({
      tone: PropTypes.oneOf(['success', 'error']),
      message: PropTypes.string,
      files: PropTypes.array,
    }),
    canExport: PropTypes.bool,
  }).isRequired,
  weekPicker: PropTypes.object,
  onNavigate: PropTypes.func,
}
