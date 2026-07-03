/**
 * Pipeline state for the app — the human runs each stage manually.
 * Stages 1-4 are run from the Dashboard; stage 5 (Human Score) is completed
 * by submitting the report on the Dashboard.
 *
 * TODO (backend task): connect calls in src/api/* when FastAPI is ready.
 */
import { useState, useEffect, useCallback } from 'react'
import {
  getAgentOutputs,
  getAvailableWeeks,
  getStageLogs,
  runStage as apiRunStage,
} from '../api'
import { todayIso, dateToWeekLabel } from '../lib/date'
import { emptyAgentOutputs } from '../lib/defaults'
import {
  DEMO_FINAL_ACCURACY,
  exampleIdlePipeline,
  exampleSavedWeekPipeline,
  exampleStages,
} from '../lib/exampleData'

const TOTAL_STAGES = 5
const AI_STAGES = 4 // stages 1-4 run automatically per click; stage 5 is the human report

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
  const [error, setError] = useState(null)

  const currentWeek = selectedWeek || dateToWeekLabel(predictionDate)
  const doneCount = pipeline.stages.filter(s => s.status === 'success').length
  const isRunning = pipeline.isRunning
  const allDone = doneCount >= TOTAL_STAGES
  const aiComplete = doneCount >= AI_STAGES

  const clearError = useCallback(() => setError(null), [])

  const fetchWeeks = useCallback(async () => {
    try {
      const data = await getAvailableWeeks()
      setSavedWeeks(data.weeks || [])
      if (data.currentDate) setPredictionDate(data.currentDate)
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
  function completeReview() {
    const stageLog = getStageLogs(AI_STAGES)
    setLogs(prev => [...prev, ...stageLog.start, ...stageLog.done])
    setPipeline(prev => ({
      ...prev,
      isRunning: false,
      currentStage: AI_STAGES,
      stages: exampleStages(TOTAL_STAGES, -1),
      accuracy: DEMO_FINAL_ACCURACY,
      lastRun: new Date().toISOString(),
    }))
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
