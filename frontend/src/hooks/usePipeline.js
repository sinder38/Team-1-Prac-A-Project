/**
 * Pipeline state for the app — the human runs each stage manually.
 * Stages 1-4 are run from the Dashboard; stage 5 (Human Score) is completed
 * by submitting the report on the Dashboard.
 *
 * TODO (backend task): connect calls in src/api/* when FastAPI is ready.
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  getAgentOutputs,
  getAvailableWeeks,
  getStageLogs,
  runStage as apiRunStage,
} from '../api'
import { todayIso, dateToWeekLabel } from '../lib/date'
import { buildHumanScoreReport } from '../lib/humanScore'
import { emptyAgentOutputs } from '../lib/defaults'
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
  const { week: _week, ...agents } = data || {}
  return {
    ...emptyAgentOutputs,
    ...Object.fromEntries(Object.entries(agents).filter(([, v]) => v != null)),
  }
}

export function usePipeline() {
  const [pipeline, setPipeline] = useState(exampleIdlePipeline())
  const [logs, setLogs] = useState([])
  const [outputs, setOutputs] = useState(emptyAgentOutputs)
  const [predictionDate, setPredictionDate] = useState(todayIso())
  const [selectedWeek, setSelectedWeek] = useState(null)
  const [savedWeeks, setSavedWeeks] = useState([])
  const [humanScoreReports, setHumanScoreReports] = useState(readStoredReports)
  const [error, setError] = useState(null)

  const currentWeek = selectedWeek || dateToWeekLabel(predictionDate)
  const doneCount = pipeline.stages.filter(s => s.status === 'success').length
  const isRunning = pipeline.isRunning
  const allDone = doneCount >= TOTAL_STAGES
  const aiComplete = doneCount >= AI_STAGES

  const humanScoreReport = useMemo(() => {
    if (!allDone) return null
    if (humanScoreReports[currentWeek]) return humanScoreReports[currentWeek]
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

  const fetchWeeks = useCallback(async () => {
    try {
      const data = await getAvailableWeeks()
      setSavedWeeks(mergeSavedWeeks(data.weeks, readStoredReports()))
    } catch (err) {
      setError(errorMessage(err, 'Could not load saved weeks'))
    }
  }, [])

  useEffect(() => { fetchWeeks() }, [fetchWeeks])

  function resetRun() {
    setError(null)
    setPipeline(prev => ({
      ...prev,
      isRunning: false,
      currentStage: 0,
      stages: exampleStages(0, -1),
      accuracy: 0,
      lastRun: null,
    }))
    setLogs([])
    setOutputs(emptyAgentOutputs)
  }

  // Run one AI stage (index 0-3). Only the next pending stage can be run.
  async function runStage(index) {
    if (isRunning || index !== doneCount || index >= AI_STAGES) return

    setError(null)
    const stageLog = getStageLogs(index)
    setPipeline(prev => ({
      ...prev,
      isRunning: true,
      currentStage: index,
      stages: exampleStages(index, index),
      week: currentWeek,
      predictionDate,
    }))
    setLogs(prev => [...prev, ...stageLog.start])

    try {
      await apiRunStage(index)

      // Reveal outputs progressively: agents after stage 2, LLM after stage 3.
      if (index === 1 || index === 2) {
        const data = await getAgentOutputs(currentWeek)
        setOutputs(prev =>
          index === 1
            ? { ...prev, almanac: data.almanac, macro: data.macro, technical: data.technical }
            : { ...prev, llmComparison: data.llmComparison },
        )
      }

      setLogs(prev => [...prev, ...stageLog.done])
      setPipeline(prev => ({
        ...prev,
        isRunning: false,
        currentStage: index,
        stages: exampleStages(index + 1, -1),
      }))
    } catch (err) {
      setError(errorMessage(err, `Stage ${index + 1} failed`))
      // Roll the stage back to pending so the user can retry.
      setPipeline(prev => ({
        ...prev,
        isRunning: false,
        stages: exampleStages(index, -1),
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
    setLogs(prev => [...prev, ...stageLog.start, ...stageLog.done])
    setPipeline(prev => ({
      ...prev,
      isRunning: false,
      currentStage: AI_STAGES,
      stages: exampleStages(TOTAL_STAGES, -1),
      accuracy: DEMO_FINAL_ACCURACY,
      lastRun: new Date().toISOString(),
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
    // ponytail: demo has no backend yet — keep the finished week in the dropdown for this session
    setSavedWeeks(prev =>
      prev.some(w => w.week === currentWeek)
        ? prev
        : [...prev, { week: currentWeek, predictionDate }].sort((a, b) => a.week.localeCompare(b.week)),
    )
  }

  function onDateChange(date) {
    setError(null)
    setPredictionDate(date)
    const week = dateToWeekLabel(date)
    setSelectedWeek(week)
    setLogs([])
    setOutputs(emptyAgentOutputs)
    setPipeline(exampleIdlePipeline(week, date))
  }

  // Selecting a saved week shows its stored (already-complete) outputs.
  async function onWeekSelect(entry) {
    setError(null)
    setSelectedWeek(entry.week)
    setPredictionDate(entry.predictionDate)
    setLogs([])
    try {
      const data = await getAgentOutputs(entry.week)
      setOutputs(pickAgentOutputs(data))
      setPipeline(exampleSavedWeekPipeline(entry.week, entry.predictionDate))
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
    humanScoreReport,
    doneCount,
    isRunning,
    allDone,
    aiComplete,
    totalStages: TOTAL_STAGES,
    aiStages: AI_STAGES,
    onDateChange,
    onWeekSelect,
    runStage,
    runNext,
    resetRun,
    completeReview,
  }
}
