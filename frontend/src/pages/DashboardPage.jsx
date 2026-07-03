/**
 * Home page: run the pipeline stage by stage and see agent results.
 */
import PropTypes from 'prop-types'
import { ClipboardCheck } from 'lucide-react'
import { PipelineController } from '../components/pipeline'
import { AgentOutputsGrid } from '../components/agents'
import { ReviewForm } from '../components/review'

export default function DashboardPage({ pipeline, outputs, controls, onNavigate, onCompleteReview, weekPicker }) {
  return (
    <div className="flex-1 overflow-auto">
      <PipelineController
        pipeline={pipeline}
        controls={controls}
        onNavigate={onNavigate}
        weekPicker={weekPicker}
      />

      {controls.aiComplete && (
        <div className="mx-4 mt-4">
          <div className="flex items-center gap-2 mb-3">
            <ClipboardCheck className="w-5 h-5 text-gray-500" />
            <h2 className="text-base font-semibold text-gray-900">Human Score Report</h2>
          </div>
          <ReviewForm
            outputs={outputs}
            week={weekPicker?.selectedWeek || pipeline?.week || '—'}
            aiComplete={controls.aiComplete}
            onComplete={onCompleteReview}
          />
        </div>
      )}

      <AgentOutputsGrid outputs={outputs} />
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
}
