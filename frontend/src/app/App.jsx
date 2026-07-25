/**
 * Main layout: sidebar, top bar, and page switching.
 */
import { useState } from 'react'
import { LeftNavigation, TopHeader } from '../components/layout'
import {
  DashboardPage,
  ChartsPage,
  LogsPage,
  CalibrationPage,
  SettingsPage,
} from '../pages'
import { usePipeline } from '../hooks/usePipeline'

export default function App() {
  const [page, setPage] = useState('dashboard')
  const pipeline = usePipeline()

  const weekPicker = {
    predictionDate: pipeline.predictionDate,
    selectedWeek: pipeline.selectedWeek,
    selectedRunId: pipeline.selectedRunId,
    savedWeeks: pipeline.savedWeeks,
    onDateChange: pipeline.onDateChange,
    onWeekSelect: pipeline.onWeekSelect,
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
        weekPicker={weekPicker}
        humanScoreReport={pipeline.humanScoreReport}
      />
    ),
    charts: <ChartsPage />,
    logs: (
      <LogsPage
        pipeline={pipeline.pipeline}
        controls={controls}
        week={pipeline.selectedWeek}
        predictionDate={pipeline.predictionDate}
      />
    ),
    calibration: <CalibrationPage pipeline={pipeline.pipeline} />,
    settings: <SettingsPage />,
  }

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900">
      <aside className="shrink-0 self-stretch flex items-start px-3 pt-4">
        <LeftNavigation active={page} onChange={setPage} />
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden min-w-0 px-4 pt-4">
        <TopHeader page={page} />
        {pages[page] || pages.dashboard}
      </div>
    </div>
  )
}
