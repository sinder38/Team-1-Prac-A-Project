/**
 * Dashboard: pipeline controls, week snapshot, reports, agents, evidence.
 */
import PropTypes from 'prop-types'
import { PipelineController } from '../components/pipeline'
import { AgentOutputsGrid, EvidenceGallery } from '../components/agents'
import {
  ReviewForm,
  HumanScoreReportCard,
  FinalPredictionForm,
  FinalPredictionReportCard,
} from '../components/review'

export default function DashboardPage({
  pipeline,
  outputs,
  controls,
  onNavigate,
  onCompleteReview,
  onCompleteFinalPrediction,
  weekPicker,
  humanScoreReport,
  finalPrediction,
}) {
  const week = weekPicker?.selectedWeek || pipeline?.week || '—'
  const predictionDate = weekPicker?.predictionDate || pipeline?.predictionDate
  const showTeamReports = Boolean(humanScoreReport || finalPrediction)
  const hasOutputs = Boolean(
    outputs?.almanac || outputs?.macro || outputs?.technical || outputs?.llmComparison,
  )
  const readingMode = (hasOutputs || showTeamReports) && !controls.isRunning

  return (
    <div className="flex-1 overflow-auto pb-6">
      <PipelineController
        pipeline={pipeline}
        controls={controls}
        onNavigate={onNavigate}
        weekPicker={weekPicker}
        defaultCollapsed={readingMode}
      />

      {controls.canEdit && controls.aiComplete && !controls.allDone && !humanScoreReport && (
        <div className="mx-4 mt-4">
          <ReviewForm
            outputs={outputs}
            week={week}
            aiComplete={controls.aiComplete}
            onComplete={onCompleteReview}
          />
        </div>
      )}

      <AgentOutputsGrid outputs={outputs} />

      {showTeamReports && (
        <section className="mx-4 pb-2 pt-4">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
            {humanScoreReport && (
              <div className="min-w-0">
                <HumanScoreReportCard report={humanScoreReport} />
              </div>
            )}

            {(finalPrediction || controls.canEdit) && (
              <div className="min-w-0">
                {finalPrediction ? (
                  <FinalPredictionReportCard report={finalPrediction} />
                ) : (
                  <FinalPredictionForm
                    week={week}
                    predictionDate={predictionDate}
                    hsrReady={Boolean(humanScoreReport)}
                    onComplete={onCompleteFinalPrediction}
                  />
                )}
              </div>
            )}
          </div>
        </section>
      )}

      <EvidenceGallery week={week} />
    </div>
  )
}

DashboardPage.propTypes = {
  pipeline: PropTypes.object.isRequired,
  outputs: PropTypes.object,
  controls: PropTypes.object.isRequired,
  onNavigate: PropTypes.func,
  onCompleteReview: PropTypes.func,
  onCompleteFinalPrediction: PropTypes.func,
  weekPicker: PropTypes.object,
  humanScoreReport: PropTypes.object,
  finalPrediction: PropTypes.object,
}
