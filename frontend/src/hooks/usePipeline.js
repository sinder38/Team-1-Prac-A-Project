/**
 * Pipeline state for the app — the human runs each stage manually.
 * Stages 1-4 are run from the Dashboard; stage 5 (Human Score) is completed
 * by submitting the report on the Dashboard. Stages 1-2 call the real backend
 * (see src/api/pipeline.js and src/api/agents.js). HSR is stored per run_id.
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  getAgentOutputs,
  getAvailableWeeks,
  getLlmModels,
  getStageLogs,
  runStage as apiRunStage,
  exportArtifacts as apiExportArtifacts,
  submitHumanScore,
  submitFinalPrediction,
  DEFAULT_HORIZON_DAYS,
} from '../api'
import { todayIso, dateToWeekLabel } from '../lib/date'
import { buildHumanScoreReport } from '../lib/humanScore'
import { buildFinalPredictionReport } from '../lib/finalPrediction'
import { emptyAgentOutputs } from '../lib/defaults'
import { inferProviderMode } from '../lib/llmProvider'
import {
  DEMO_FINAL_ACCURACY,
  exampleHumanScoreFormForWeek,
  exampleIdlePipeline,
  exampleSavedWeekPipeline,
  exampleStages,
  isExampleWeek,
} from '../lib/exampleData'

const TOTAL_STAGES = 5
const AI_STAGES = 4 // stages 1-4 run automatically per click; stage 5 is the human report
const LLM_STAGE_INDEX = 2 // 0-based; keep in sync with PipelineController
const HSR_STORAGE_KEY = 'humanScoreReports'
const FP_STORAGE_KEY = 'finalPredictions'
const DEFAULT_PROVIDER_MODE = 'ollama'

function modelsForProvider(models, provider) {
  return models.filter(m => (m.provider || 'openrouter') === provider)
}

function keysForProvider(models, provider) {
  return modelsForProvider(models, provider).map(m => m.key)
}

function makeRunId() {
  return `run-${Date.now().toString(36)}`
}

function readStoredReports(key = HSR_STORAGE_KEY) {
  try {
    const raw = sessionStorage.getItem(key)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function writeStoredReports(reports, key = HSR_STORAGE_KEY) {
  try {
    sessionStorage.setItem(key, JSON.stringify(reports))
  } catch {
    /* quota / private mode */
  }
}

/** HSR cache key — runtime runs use run_id; archives use week label. */
function hsrKey({ runId, week } = {}) {
  if (runId) return `run:${runId}`
  if (week) return `week:${week}`
  return null
}

function lookupHsr(reports, { runId, week, allowWeekFallback = false } = {}) {
  if (!reports) return null
  const byRun = runId ? reports[hsrKey({ runId })] : null
  if (byRun) return byRun
  // Week keys are for markdown archives only — never leak onto a runtime run.
  if (!allowWeekFallback) return null
  if (week && reports[week]) return reports[week]
  if (week && reports[hsrKey({ week })]) return reports[hsrKey({ week })]
  return null
}

function mergeSavedWeeks(apiWeeks, storedReports) {
  const merged = [...(apiWeeks || [])]
  for (const report of Object.values(storedReports || {})) {
    const week = report?.week
    if (!week) continue
    const runId = report.runId || null
    if (!merged.some(w => w.week === week && (w.runId || null) === runId)) {
      merged.push({
        week,
        predictionDate: report.predictionDate ?? todayIso(),
        runId,
        source: runId ? 'run' : 'archive',
      })
    }
  }
  // Multiple run_ids can share a week (prediction_run schema).
  return merged.sort(
    (a, b) =>
      a.week.localeCompare(b.week) ||
      String(a.runId || '').localeCompare(String(b.runId || '')),
  )
}

function errorMessage(err, fallback) {
  return err?.message ? `${fallback}: ${err.message}` : fallback
}

/** Keep only the agent keys that actually have data (drops the `week` field). */
function pickAgentOutputs(data) {
  const {
    week: _week,
    humanScoreReport: _hs,
    finalPrediction: _fp,
    ...agents
  } = data || {}
  return {
    ...emptyAgentOutputs,
    ...Object.fromEntries(Object.entries(agents).filter(([, v]) => v != null)),
  }
}

/** How far the pipeline UI should look finished for a loaded week. */
function doneCountFromArtifacts({ hasAgents, hasLlm, hasHsr }) {
  if (hasHsr) return TOTAL_STAGES
  if (hasLlm) return LLM_STAGE_INDEX + 1
  if (hasAgents) return 2
  return 0
}

/** Infer Local vs Real API from loaded LLM consensus. */
async function resolveProviderFromLlm(llmComparison, availableModels) {
  const models = availableModels.length ? availableModels : await getLlmModels()
  const mode = inferProviderMode(llmComparison, models)
  return {
    models,
    mode,
    selectedKeys: mode ? keysForProvider(models, mode) : null,
  }
}

export function usePipeline() {
  const [runId, setRunId] = useState(() => makeRunId())
  const [pipeline, setPipeline] = useState(() => exampleIdlePipeline())
  const [logs, setLogs] = useState([])
  const [outputs, setOutputs] = useState(emptyAgentOutputs)
  const [predictionDate, setPredictionDate] = useState(todayIso())
  const [horizonDays, setHorizonDays] = useState(DEFAULT_HORIZON_DAYS)
  const [selectedWeek, setSelectedWeek] = useState(null)
  // Which saved run is open (null = new run or markdown archive without run_id).
  const [selectedRunId, setSelectedRunId] = useState(null)
  const [savedWeeks, setSavedWeeks] = useState([])
  const [humanScoreReports, setHumanScoreReports] = useState(() => readStoredReports())
  const [finalPredictions, setFinalPredictions] = useState(() => readStoredReports(FP_STORAGE_KEY))
  const [error, setError] = useState(null)
  const [availableModels, setAvailableModels] = useState([])
  const [selectedModels, setSelectedModels] = useState(null)
  const [providerMode, setProviderModeState] = useState(DEFAULT_PROVIDER_MODE)
  // 'new' = idle/live run; 'archive' = viewing a saved week/run
  const [weekPickerMode, setWeekPickerMode] = useState('new')
  // Calendar-chosen week kept in the selector after switching to a past run.
  const [newPredictionDate, setNewPredictionDate] = useState(todayIso)
  const newWeek = dateToWeekLabel(newPredictionDate)
  const [exporting, setExporting] = useState(false)
  const [exportStatus, setExportStatus] = useState(null)

  // Keep Logs "Run ID" in sync for live runs (pipeline.id === API runId).
  // Archive weeks set pipeline.id to archive-WXX separately without changing API runId.
  useEffect(() => {
    setPipeline(prev => {
      if (prev.id?.startsWith('archive-')) return prev
      return prev.id === runId ? prev : { ...prev, id: runId }
    })
  }, [runId])

  const currentWeek = selectedWeek || dateToWeekLabel(predictionDate)
  const doneCount = pipeline.stages.filter(s => s.status === 'success').length
  const isRunning = pipeline.isRunning
  const allDone = doneCount >= TOTAL_STAGES
  const aiComplete = doneCount >= AI_STAGES

  const activeRunId = selectedRunId || runId
  // Archive markdown weeks have no run_id; runtime runs must not inherit week: cache.
  const allowWeekFallback = weekPickerMode === 'archive' && !selectedRunId

  const humanScoreReport = useMemo(() => {
    const stored = lookupHsr(humanScoreReports, {
      runId: allowWeekFallback ? null : activeRunId,
      week: currentWeek,
      allowWeekFallback,
    })
    if (stored) return stored
    if (!allDone) return null
    if (isExampleWeek(currentWeek)) {
      return buildHumanScoreReport(exampleHumanScoreFormForWeek(currentWeek), {
        week: currentWeek,
        outputs,
        predictionDate,
      })
    }
    return null
  }, [
    allDone,
    humanScoreReports,
    activeRunId,
    currentWeek,
    outputs,
    predictionDate,
    allowWeekFallback,
  ])

  const finalPrediction = useMemo(
    () =>
      lookupHsr(finalPredictions, {
        runId: allowWeekFallback ? null : activeRunId,
        week: currentWeek,
        allowWeekFallback,
      }),
    [finalPredictions, activeRunId, currentWeek, allowWeekFallback],
  )

  const clearError = useCallback(() => setError(null), [])

  function clearHumanScoreForRun(id, week) {
    const key = hsrKey({ runId: id, week })
    if (!key) return
    setHumanScoreReports(prev => {
      if (!prev[key] && !(week && prev[week])) return prev
      const next = { ...prev }
      delete next[key]
      if (week) delete next[week]
      writeStoredReports(next)
      return next
    })
    setFinalPredictions(prev => {
      if (!prev[key] && !(week && prev[week])) return prev
      const next = { ...prev }
      delete next[key]
      if (week) delete next[week]
      writeStoredReports(next, FP_STORAGE_KEY)
      return next
    })
  }

  const fetchWeeks = useCallback(async () => {
    try {
      const data = await getAvailableWeeks()
      setSavedWeeks(mergeSavedWeeks(data.weeks, readStoredReports()))
    } catch (err) {
      setError(errorMessage(err, 'Could not load saved weeks'))
    }
  }, [])

  useEffect(() => { fetchWeeks() }, [fetchWeeks])

  useEffect(() => {
    getLlmModels()
      .then(models => {
        setAvailableModels(models)
        setSelectedModels(keysForProvider(models, DEFAULT_PROVIDER_MODE))
      })
      .catch(err => setError(errorMessage(err, 'Could not load LLM model list')))
  }, [])

  const modelsForMode = useMemo(
    () => modelsForProvider(availableModels, providerMode),
    [availableModels, providerMode],
  )

  function setProviderMode(mode) {
    setProviderModeState(mode)
    setSelectedModels(keysForProvider(availableModels, mode))
  }

  function toggleModel(key) {
    setSelectedModels(prev => {
      const current = prev ?? keysForProvider(availableModels, providerMode)
      return current.includes(key) ? current.filter(k => k !== key) : [...current, key]
    })
  }

  function resetRun() {
    setError(null)
    setExportStatus(null)
    const nextId = makeRunId()
    setRunId(nextId)
    setPipeline(prev => ({
      ...prev,
      id: nextId,
      isRunning: false,
      currentStage: 0,
      stages: exampleStages(0, -1),
      accuracy: 0,
      lastRun: null,
    }))
    setLogs([])
    setOutputs(emptyAgentOutputs)
    clearHumanScoreForRun(runId, currentWeek)
  }

  // Run one AI stage (index 0-3). Only the next pending stage can be run.
  async function runStage(index) {
    if (isRunning || index !== doneCount || index >= AI_STAGES) return
    if (index === 2 && selectedModels && selectedModels.length === 0) {
      setError('Select at least one LLM model before running this stage.')
      return
    }

    setError(null)
    const stageLog = getStageLogs(index)
    setPipeline(prev => ({
      ...prev,
      isRunning: true,
      currentStage: index,
      stages: exampleStages(index, index, prev.stages),
      week: currentWeek,
      predictionDate,
    }))
    setLogs(prev => [...prev, ...stageLog.start])

    try {
      const stageResult = await apiRunStage(index, {
        predictionDate,
        runId,
        horizonDays,
        models: selectedModels,
      })

      // Reveal outputs progressively: agents after stage 2, LLM after stage 3.
      if (index === 1 || index === 2) {
        const stem = dateToWeekLabel(predictionDate).split('-').pop()
        const data = await getAgentOutputs({
          predictionDate,
          runId,
          horizonDays,
          includeLlm: index === 2,
          stem,
          source: 'run',
        })
        setOutputs(prev =>
          index === 1
            ? { ...prev, almanac: data.almanac, macro: data.macro, technical: data.technical }
            : {
                ...prev,
                llmComparison: data.llmComparison,
              },
        )
        if (index === 2 && data.humanScoreReport) {
          const key = hsrKey({ runId })
          setHumanScoreReports(prev => {
            const next = { ...prev, [key]: { ...data.humanScoreReport, runId } }
            writeStoredReports(next)
            return next
          })
        }
      }

      const partialFailures = stageResult?.failures ?? []
      if (partialFailures.length) {
        setError(`Some models failed (${partialFailures.length}):\n${partialFailures.join('\n')}`)
      }

      const finishedAt = new Date().toISOString()
      setLogs(prev => [...prev, ...stageLog.done])
      setPipeline(prev => ({
        ...prev,
        isRunning: false,
        currentStage: index,
        lastRun: finishedAt,
        stages: exampleStages(index + 1, -1, prev.stages),
      }))
      if (index === 1 || index === 2) fetchWeeks()
    } catch (err) {
      setError(errorMessage(err, `Stage ${index + 1} failed`))
      // Roll the stage back to pending so the user can retry.
      setPipeline(prev => ({
        ...prev,
        isRunning: false,
        stages: exampleStages(index, -1, prev.stages),
      }))
    }
  }

  function runNext() {
    return runStage(doneCount)
  }

  // Export the current run's stored data to data/<agent>/*.md. Archive weeks are
  // keyed by stem; live/saved runs by their real run id.
  const canExport = doneCount > 0 && !isRunning && !exporting

  async function exportArtifacts() {
    if (!canExport) return
    setExportStatus(null)
    setExporting(true)
    try {
      const isArchive = pipeline.id?.startsWith('archive-')
      const stem = isArchive ? currentWeek?.split('-').pop() : undefined
      const data = await apiExportArtifacts({ runId, stem })
      const written = data.written ?? []
      setExportStatus(
        written.length
          ? { tone: 'success', message: `Exported ${written.length} file(s) to data/`, files: written }
          : { tone: 'error', message: 'No artifacts found to export for this run.' },
      )
    } catch (err) {
      setExportStatus({ tone: 'error', message: errorMessage(err, 'Export failed') })
    } finally {
      setExporting(false)
    }
  }

  // Completing the human report marks the final stage done and persists by run_id.
  async function completeReview(form) {
    if (!form) return
    const report = {
      ...buildHumanScoreReport(form, { week: currentWeek, outputs, predictionDate }),
      runId,
    }
    try {
      await submitHumanScore({
        predictionDate,
        runId,
        horizonDays: DEFAULT_HORIZON_DAYS,
        week: currentWeek,
        form,
        consensus: report?.consensus,
        aiSaid: report?.aiSaid,
        total: report?.total,
      })
    } catch (err) {
      setError(errorMessage(err, 'Could not save human score'))
      throw err
    }

    const stageLog = getStageLogs(AI_STAGES)
    const finishedAt = new Date().toISOString()
    const key = hsrKey({ runId })
    setLogs(prev => [...prev, ...stageLog.start, ...stageLog.done])
    setPipeline(prev => ({
      ...prev,
      isRunning: false,
      currentStage: AI_STAGES,
      stages: exampleStages(TOTAL_STAGES, -1, prev.stages),
      accuracy: DEMO_FINAL_ACCURACY,
      lastRun: finishedAt,
      week: currentWeek,
      predictionDate,
    }))
    setSelectedWeek(currentWeek)
    setSelectedRunId(runId)
    setWeekPickerMode('archive')
    setHumanScoreReports(prev => {
      const next = { ...prev, [key]: report }
      writeStoredReports(next)
      return next
    })
    setSavedWeeks(prev =>
      prev.some(w => w.week === currentWeek && w.runId === runId)
        ? prev
        : [...prev, { week: currentWeek, predictionDate, runId, source: 'run' }].sort((a, b) =>
            a.week.localeCompare(b.week) || String(a.runId || '').localeCompare(String(b.runId || '')),
          ),
    )
  }

  // After HSR: lock the Team1 consensus brief (DB + markdown file for delta).
  async function completeFinalPrediction(form) {
    if (!form) return
    const report = buildFinalPredictionReport(form, {
      week: currentWeek,
      predictionDate,
      runId,
    })
    try {
      await submitFinalPrediction({ runId, report })
    } catch (err) {
      setError(errorMessage(err, 'Could not save final prediction'))
      throw err
    }
    const key = hsrKey({ runId })
    setSelectedWeek(currentWeek)
    setSelectedRunId(runId)
    setWeekPickerMode('archive')
    setFinalPredictions(prev => {
      const next = { ...prev, [key]: report }
      writeStoredReports(next, FP_STORAGE_KEY)
      return next
    })
  }

  function onDateChange(date) {
    setError(null)
    setWeekPickerMode('new')
    setSelectedRunId(null)
    setNewPredictionDate(date)
    setExportStatus(null)
    setPredictionDate(date)
    const week = dateToWeekLabel(date)
    setSelectedWeek(week)
    setLogs([])
    setOutputs(emptyAgentOutputs)
    const nextId = makeRunId()
    setRunId(nextId)
    setPipeline(exampleIdlePipeline(week, date, nextId))
  }

  function cacheLoadedReports(entry, data) {
    const key = hsrKey({ runId: entry.runId, week: entry.week })
    if (!key) return
    if (data.humanScoreReport) {
      setHumanScoreReports(prev => {
        const next = {
          ...prev,
          [key]: { ...data.humanScoreReport, runId: entry.runId || undefined },
        }
        writeStoredReports(next)
        return next
      })
    }
    if (data.finalPrediction) {
      setFinalPredictions(prev => {
        const next = {
          ...prev,
          [key]: { ...data.finalPrediction, runId: entry.runId || undefined },
        }
        writeStoredReports(next, FP_STORAGE_KEY)
        return next
      })
    }
  }

  // Selecting a saved week/run loads outputs. Only mark stages finished that have
  // real artifacts — calibration (4) and human score (5) stay pending until run.
  async function onWeekSelect(entry) {
    setError(null)
    setWeekPickerMode('archive')
    setExportStatus(null)
    setSelectedWeek(entry.week)
    setSelectedRunId(entry.runId || null)
    setPredictionDate(entry.predictionDate)
    setLogs([])
    const stem = entry.stem || entry.week?.split('-').pop()
    const isArchive = entry.source === 'archive' || !entry.runId
    // Display id for Logs; API runId stays a real run-* (or existing entry.runId).
    const displayId = entry.runId || (stem ? `archive-${stem}` : null)
    const apiRunId = entry.runId || makeRunId()

    if (!entry.runId && !stem) {
      setOutputs(emptyAgentOutputs)
      setRunId(apiRunId)
      setPipeline(exampleSavedWeekPipeline(entry.week, entry.predictionDate, displayId, { doneCount: 0 }))
      return
    }

    setRunId(apiRunId)
    try {
      const data = await getAgentOutputs({
        predictionDate: entry.predictionDate,
        runId: entry.runId,
        horizonDays,
        stem,
        source: isArchive ? 'archive' : 'run',
      })
      const outputsForWeek = pickAgentOutputs(data)
      setOutputs(outputsForWeek)

      const localHsr = lookupHsr(readStoredReports(), {
        runId: entry.runId,
        week: entry.week,
      })
      const hasAgents = Boolean(
        outputsForWeek.almanac || outputsForWeek.macro || outputsForWeek.technical,
      )
      const hasLlm = Boolean(outputsForWeek.llmComparison)
      const hasHsr = Boolean(data.humanScoreReport || localHsr)
      const doneCount = doneCountFromArtifacts({ hasAgents, hasLlm, hasHsr })

      if (hasLlm) {
        const { models, mode, selectedKeys } = await resolveProviderFromLlm(
          outputsForWeek.llmComparison,
          availableModels,
        )
        if (!availableModels.length) setAvailableModels(models)
        if (mode) {
          setProviderModeState(mode)
          setSelectedModels(selectedKeys)
        }
      }

      setPipeline(
        exampleSavedWeekPipeline(entry.week, entry.predictionDate, displayId, { doneCount }),
      )
      cacheLoadedReports(entry, data)
    } catch (err) {
      setError(errorMessage(err, `Could not load ${entry.week}`))
    }
  }

  return {
    pipeline,
    logs,
    outputs,
    error,
    clearError,
    predictionDate,
    horizonDays,
    setHorizonDays,
    selectedWeek: currentWeek,
    selectedRunId,
    savedWeeks,
    weekPickerMode,
    newWeek,
    newPredictionDate,
    runId,
    humanScoreReport,
    finalPrediction,
    doneCount,
    isRunning,
    allDone,
    aiComplete,
    totalStages: TOTAL_STAGES,
    aiStages: AI_STAGES,
    availableModels: modelsForMode,
    selectedModels: selectedModels ?? keysForProvider(availableModels, providerMode),
    providerMode,
    setProviderMode,
    toggleModel,
    onDateChange,
    onWeekSelect,
    runStage,
    runNext,
    resetRun,
    completeReview,
    completeFinalPrediction,
    exportArtifacts,
    exporting,
    exportStatus,
    canExport,
  }
}
