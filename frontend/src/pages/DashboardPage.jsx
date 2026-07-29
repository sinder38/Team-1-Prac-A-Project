/**
 * Home page: run the pipeline stage by stage and see agent results.
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

  return (
    <div className="flex-1 overflow-auto">
      <PipelineController
        pipeline={pipeline}
        controls={controls}
        onNavigate={onNavigate}
        weekPicker={weekPicker}
      />

      {controls.aiComplete && !controls.allDone && !humanScoreReport && (
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

      <EvidenceGallery week={week} />

      {showTeamReports && (
        <section className="mx-4 pb-6 pt-2">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
            {humanScoreReport && (
              <div className="min-w-0">
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-gray-900">Human Score Report</h3>
                  <p className="text-xs text-gray-500 mt-0.5">Team assessment for {week}</p>
                </div>
                <HumanScoreReportCard report={humanScoreReport} />
              </div>
            )}

            <div className="min-w-0">
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-900">Final Prediction</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {finalPrediction
                    ? `Locked consensus brief for ${week}`
                    : `File the Team1 brief for ${week}`}
                </p>
              </div>
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
          </div>
        </section>
      )}
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
