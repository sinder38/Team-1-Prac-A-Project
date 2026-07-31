/**
 * Bias chips for the selected week; conflict banner when sources disagree.
 */
import PropTypes from 'prop-types'
import { AlertTriangle } from 'lucide-react'
import { biasBadgeClass } from '../../lib/agentDisplay'
import { buildWeekSummary } from '../../lib/weekSummary'

export default function WeekSummaryStrip({ week, outputs, finalPrediction }) {
  const { signals, conflict, hasSignals } = buildWeekSummary({ outputs, finalPrediction })
  if (!hasSignals) return null

  return (
    <section className="mx-4 mt-4 rounded-xl border border-gray-200 bg-white shadow-md px-4 py-3">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
        <div>
          <h3 className="text-sm font-medium text-gray-900">Week snapshot</h3>
          <p className="text-xs text-gray-500 mt-0.5">{week || '—'}</p>
        </div>
        {conflict && (
          <p className="inline-flex items-start gap-1.5 text-xs font-medium text-amber-800 bg-amber-50 ring-1 ring-amber-600/15 rounded-md px-2.5 py-1.5 max-w-xl">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>
              <span className="font-semibold">Conflict · </span>
              {conflict}
            </span>
          </p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {signals.map(s => (
          <div
            key={s.id}
            className="flex items-center gap-2 rounded-lg border border-gray-100 bg-gray-50/80 px-2.5 py-1.5"
          >
            <span className="text-[11px] font-medium uppercase tracking-wide text-gray-400">
              {s.label}
            </span>
            <span
              className={`text-[11px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full ring-1 ${biasBadgeClass(s.tone)}`}
            >
              {s.text}
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}

WeekSummaryStrip.propTypes = {
  week: PropTypes.string,
  outputs: PropTypes.object,
  finalPrediction: PropTypes.object,
}
