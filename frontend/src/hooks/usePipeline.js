/**
 * Pipeline state for the app — the human runs each stage manually.
 * Stages 1-4 are run from the Dashboard; stage 5 (Human Score) is completed
 * by submitting the report on the Dashboard. Stages 1-2 call the real backend
 * (see src/api/pipeline.js and src/api/agents.js). Human-score submission is
 * still local-only until the backend supports it.
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  getAgentOutputs,
  getAvailableWeeks,
  getLlmModels,
  getStageLogs,
  runStage as apiRunStage,
  DEFAULT_HORIZON_DAYS,
} from '../api'
import { todayIso, dateToWeekLabel } from '../lib/date'
import { buildHumanScoreReport } from '../lib/humanScore'
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
const HSR_STORAGE_KEY = 'humanScoreReports'
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

function readStoredReports() {
  try {
    const raw = sessionStorage.getItem(HSR_STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function writeStoredReports(reports) {
  try {
    sessionStorage.setItem(HSR_STORAGE_KEY, JSON.stringify(reports))
  } catch {
    /* quota / private mode */
  }
}

function mergeSavedWeeks(apiWeeks, storedReports) {
  const merged = [...(apiWeeks || [])]
  for (const [week, report] of Object.entries(storedReports)) {
    if (!merged.some(w => w.week === week)) {
      merged.push({ week, predictionDate: report.predictionDate ?? todayIso() })
    }
  }
  return merged.sort((a, b) => a.week.localeCompare(b.week))
}

function errorMessage(err, fallback) {
  return err?.message ? `${fallback}: ${err.message}` : fallback
}

/** Keep only the agent keys that actually have data (drops the `week` field). */
function pickAgentOutputs(data) {
  const { week: _week, humanScoreReport: _hs, ...agents } = data || {}
  return {
    ...emptyAgentOutputs,
    ...Object.fromEntries(Object.entries(agents).filter(([, v]) => v != null)),
  }
}

export function usePipeline() {
  const [runId, setRunId] = useState(() => makeRunId())
  const [pipeline, setPipeline] = useState(() => exampleIdlePipeline())
  const [logs, setLogs] = useState([])
  const [outputs, setOutputs] = useState(emptyAgentOutputs)
  const [predictionDate, setPredictionDate] = useState(todayIso())
  const [selectedWeek, setSelectedWeek] = useState(null)
  const [savedWeeks, setSavedWeeks] = useState([])
  const [humanScoreReports, setHumanScoreReports] = useState(readStoredReports)
  const [error, setError] = useState(null)
  const [availableModels, setAvailableModels] = useState([])
  const [selectedModels, setSelectedModels] = useState(null)
  const [providerMode, setProviderModeState] = useState(DEFAULT_PROVIDER_MODE)

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

  const humanScoreReport = useMemo(() => {
    if (humanScoreReports[currentWeek]) return humanScoreReports[currentWeek]
    if (!allDone) return null
    if (isExampleWeek(currentWeek)) {
      return buildHumanScoreReport(exampleHumanScoreFormForWeek(currentWeek), {
        week: currentWeek,
        outputs,
        predictionDate,
      })
    }
    return null
  }, [allDone, humanScoreReports, currentWeek, outputs, predictionDate])

  const clearError = useCallback(() => setError(null), [])

  function clearHumanScoreForWeek(week) {
    setHumanScoreReports(prev => {
      if (!prev[week]) return prev
      const next = { ...prev }
      delete next[week]
      writeStoredReports(next)
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
    clearHumanScoreForWeek(currentWeek)
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
        horizonDays: DEFAULT_HORIZON_DAYS,
        models: selectedModels,
      })

      // Reveal outputs progressively: agents after stage 2, LLM after stage 3.
      if (index === 1 || index === 2) {
        const stem = dateToWeekLabel(predictionDate).split('-').pop()
        const data = await getAgentOutputs({
          predictionDate,
          runId,
          horizonDays: DEFAULT_HORIZON_DAYS,
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
          setHumanScoreReports(prev => {
            const next = { ...prev, [currentWeek]: data.humanScoreReport }
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

  // Completing the human report marks the final stage done.
  function completeReview(form) {
    if (!form) return

    const stageLog = getStageLogs(AI_STAGES)
    const finishedAt = new Date().toISOString()
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
    setHumanScoreReports(prev => {
      const next = {
        ...prev,
        [currentWeek]: buildHumanScoreReport(form, { week: currentWeek, outputs, predictionDate }),
      }
      writeStoredReports(next)
      return next
    })
    setSavedWeeks(prev =>
      prev.some(w => w.week === currentWeek)
        ? prev
        : [...prev, { week: currentWeek, predictionDate, runId }].sort((a, b) => a.week.localeCompare(b.week)),
    )
  }

  function onDateChange(date) {
    setError(null)
    setPredictionDate(date)
    const week = dateToWeekLabel(date)
    setSelectedWeek(week)
    setLogs([])
    setOutputs(emptyAgentOutputs)
    const nextId = makeRunId()
    setRunId(nextId)
    setPipeline(exampleIdlePipeline(week, date, nextId))
  }

  // Selecting a saved week loads outputs. Only mark stages finished that have
  // real artifacts — calibration (4) and human score (5) stay pending until run.
  async function onWeekSelect(entry) {
    setError(null)
    setSelectedWeek(entry.week)
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
      clearHumanScoreForWeek(entry.week)
      return
    }

    setRunId(apiRunId)
    try {
      const data = await getAgentOutputs({
        predictionDate: entry.predictionDate,
        runId: entry.runId,
        horizonDays: DEFAULT_HORIZON_DAYS,
        stem,
        source: isArchive ? 'archive' : 'run',
      })
      const outputsForWeek = pickAgentOutputs(data)
      setOutputs(outputsForWeek)

      const hasAgents = Boolean(
        outputsForWeek.almanac || outputsForWeek.macro || outputsForWeek.technical,
      )
      const hasLlm = Boolean(outputsForWeek.llmComparison)
      const hasHsr = Boolean(data.humanScoreReport)
      // Stages: 0 data, 1 agents, 2 LLM, 3 calibration, 4 human score
      let doneCount = 0
      if (hasAgents) doneCount = 2
      if (hasLlm) doneCount = 3
      if (hasHsr) doneCount = TOTAL_STAGES

      // Stage 3 radio should match the loaded consensus (OpenRouter vs Ollama).
      if (hasLlm) {
        const models = availableModels.length ? availableModels : await getLlmModels()
        if (!availableModels.length) setAvailableModels(models)
        const mode = inferProviderMode(outputsForWeek.llmComparison, models)
        if (mode) {
          setProviderModeState(mode)
          setSelectedModels(keysForProvider(models, mode))
        }
      }

      setPipeline(
        exampleSavedWeekPipeline(entry.week, entry.predictionDate, displayId, { doneCount }),
      )
      setHumanScoreReports(prev => {
        const next = { ...prev }
        if (data.humanScoreReport) {
          next[entry.week] = data.humanScoreReport
        } else {
          delete next[entry.week]
        }
        writeStoredReports(next)
        return next
      })
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
    selectedWeek: currentWeek,
    savedWeeks,
    runId,
    humanScoreReport,
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
  }
}
