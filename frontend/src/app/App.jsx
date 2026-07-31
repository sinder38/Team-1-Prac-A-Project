/**
 * Main layout: sidebar, top bar, and page switching.
 */
import { useEffect, useState } from 'react'
import { LeftNavigation, TopHeader } from '../components/layout'
import {
  DashboardPage,
  ChartsPage,
  LogsPage,
  CalibrationPage,
  SettingsPage,
} from '../pages'
import { usePipeline } from '../hooks/usePipeline'
import { useTheme } from '../hooks/useTheme'
import { readPageFromUrl, syncUrl } from '../lib/appRoute'

export default function App() {
  const [page, setPage] = useState(readPageFromUrl)
  const pipeline = usePipeline()
  const { theme, toggleTheme } = useTheme()

  let status = 'idle'
  let statusLabel = 'Idle'
  if (pipeline.isRunning) {
    status = 'running'
    statusLabel = 'Running'
  } else if (pipeline.allDone) {
    status = 'complete'
    statusLabel = 'Complete'
  } else if (pipeline.doneCount > 0) {
    status = 'progress'
    statusLabel = 'In progress'
  }

  useEffect(() => {
    syncUrl({ page, week: pipeline.selectedWeek })
  }, [page, pipeline.selectedWeek])

  const weekPicker = {
    predictionDate: pipeline.predictionDate,
    selectedWeek: pipeline.selectedWeek,
    selectedRunId: pipeline.selectedRunId,
    savedWeeks: pipeline.savedWeeks,
    onDateChange: pipeline.onDateChange,
    onWeekSelect: pipeline.onWeekSelect,
    horizonDays: pipeline.horizonDays,
    onHorizonChange: pipeline.setHorizonDays,
    mode: pipeline.weekPickerMode,
    newWeek: pipeline.newWeek,
    newPredictionDate: pipeline.newPredictionDate,
  }

  const controls = {
    doneCount: pipeline.doneCount,
    isRunning: pipeline.isRunning,
    allDone: pipeline.allDone,
    aiComplete: pipeline.aiComplete,
    aiStages: pipeline.aiStages,
    error: pipeline.error,
    clearError: pipeline.clearError,
    runStage: pipeline.runStage,
    runNext: pipeline.runNext,
    resetRun: pipeline.resetRun,
    runId: pipeline.runId,
    exportArtifacts: pipeline.exportArtifacts,
    exporting: pipeline.exporting,
    exportStatus: pipeline.exportStatus,
    canExport: pipeline.canExport,
    availableModels: pipeline.availableModels,
    selectedModels: pipeline.selectedModels,
    providerMode: pipeline.providerMode,
    setProviderMode: pipeline.setProviderMode,
    toggleModel: pipeline.toggleModel,
  }

  const pages = {
    dashboard: (
      <DashboardPage
        pipeline={pipeline.pipeline}
        outputs={pipeline.outputs}
        controls={controls}
        onNavigate={setPage}
        onCompleteReview={pipeline.completeReview}
        onCompleteFinalPrediction={pipeline.completeFinalPrediction}
        weekPicker={weekPicker}
        humanScoreReport={pipeline.humanScoreReport}
        finalPrediction={pipeline.finalPrediction}
      />
    ),
    charts: (
      <ChartsPage
        predictionDate={pipeline.predictionDate}
        week={pipeline.selectedWeek}
        technical={pipeline.outputs.technical}
        macro={pipeline.outputs.macro}
        finalPrediction={pipeline.finalPrediction}
      />
    ),
    logs: (
      <LogsPage
        pipeline={pipeline.pipeline}
        controls={controls}
        week={pipeline.selectedWeek}
        predictionDate={pipeline.predictionDate}
        onNavigate={setPage}
      />
    ),
    calibration: <CalibrationPage pipeline={pipeline.pipeline} />,
    settings: <SettingsPage />,
  }

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900">
      <aside className="shrink-0 self-stretch flex items-start px-3 pt-4">
        <LeftNavigation
          active={page}
          onChange={setPage}
          theme={theme}
          onToggleTheme={toggleTheme}
        />
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden min-w-0 px-4 pt-4">
        <TopHeader
          page={page}
          week={pipeline.selectedWeek}
          runId={pipeline.runId || pipeline.pipeline?.id}
          status={status}
          statusLabel={statusLabel}
        />
        {pages[page] || pages.dashboard}
      </div>
    </div>
  )
}
