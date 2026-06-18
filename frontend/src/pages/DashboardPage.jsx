/**
 * Home page: run the pipeline stage by stage and see agent results.
 */
import { ClipboardCheck } from 'lucide-react'
import { PipelineController } from '../components/pipeline'
import { AgentOutputsGrid } from '../components/agents'

export default function DashboardPage({ pipeline, outputs, controls, onNavigate, weekPicker }) {
  const showReview = controls.aiComplete && !controls.allDone

  return (
    <div className="flex-1 overflow-auto">
      <PipelineController
        pipeline={pipeline}
        controls={controls}
        onNavigate={onNavigate}
        weekPicker={weekPicker}
      />

      {showReview && (
        <div className="mx-4 mt-3">
          <button
            onClick={() => onNavigate('review')}
            className="w-full flex items-center justify-between px-4 py-3 bg-white border border-gray-200 rounded-lg hover:border-gray-300 text-left"
          >
            <div>
              <p className="text-sm font-medium text-gray-900">Human score pending</p>
              <p className="text-xs text-gray-500 mt-0.5">
                AI stages are complete — fill in and submit your score report
              </p>
            </div>
            <ClipboardCheck className="w-5 h-5 text-gray-400 shrink-0" />
          </button>
        </div>
      )}

      <AgentOutputsGrid outputs={outputs} />
    </div>
  )
}
