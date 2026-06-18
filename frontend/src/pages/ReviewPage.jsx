/**
 * Page where the human fills in and submits the Human Score report.
 */
import { ClipboardCheck } from 'lucide-react'
import { ReviewForm } from '../components/review'

export default function ReviewPage({ outputs, week, aiComplete, onComplete }) {
  return (
    <div className="flex-1 overflow-auto p-4 md:p-6">
      <div className="flex items-center gap-2 mb-1">
        <ClipboardCheck className="w-5 h-5 text-gray-500" />
        <h2 className="text-lg font-semibold">Human Score Report</h2>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Fill in the blanks below, then submit to complete the final pipeline stage.
      </p>
      <ReviewForm
        outputs={outputs}
        week={week}
        aiComplete={aiComplete}
        onComplete={onComplete}
      />
    </div>
  )
}
