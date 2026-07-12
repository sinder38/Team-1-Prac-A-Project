/**
 * Home page: run the pipeline stage by stage and see agent results.
 */
import PropTypes from 'prop-types'
import { PipelineController } from '../components/pipeline'
import { AgentOutputsGrid } from '../components/agents'
import { ReviewForm, HumanScoreReportCard } from '../components/review'

export default function DashboardPage({
  pipeline,
  outputs,
  controls,
  onNavigate,
  onCompleteReview,
  weekPicker,
  humanScoreReport,
}) {
  const week = weekPicker?.selectedWeek || pipeline?.week || '—'

  return (
    <div className="flex-1 overflow-auto">
      <PipelineController
        pipeline={pipeline}
        controls={controls}
        onNavigate={onNavigate}
        weekPicker={weekPicker}
      />

      {controls.aiComplete && !controls.allDone && (
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

      {controls.allDone && humanScoreReport && (
        <section className="mx-4 pb-6 pt-2">
          <div className="max-w-3xl">
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-900">Human Score Report</h3>
              <p className="text-xs text-gray-500 mt-0.5">Team assessment for {week}</p>
            </div>
            <HumanScoreReportCard report={humanScoreReport} />
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
  weekPicker: PropTypes.object,
  humanScoreReport: PropTypes.object,
}
