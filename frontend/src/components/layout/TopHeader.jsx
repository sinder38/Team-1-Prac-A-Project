/**
 * Top bar: page title, week / run / pipeline status, and auth.
 */
import PropTypes from 'prop-types'
import { PAGE_TITLES } from '../../lib/constants'
import { AuthControl } from '../auth'

const STATUS_TONE = {
  running: 'bg-blue-50 text-blue-700',
  complete: 'bg-green-50 text-green-700',
  progress: 'bg-amber-50 text-amber-800',
  idle: 'bg-gray-50 text-gray-500',
}

export default function TopHeader({
  page = 'dashboard',
  week,
  runId,
  status = 'idle',
  statusLabel = 'Idle',
  auth,
}) {
  const { section, page: title } = PAGE_TITLES[page] || PAGE_TITLES.dashboard
  const shortRun = runId && runId.length > 18 ? `${runId.slice(0, 16)}…` : runId

  return (
    <header className="w-full min-h-12 rounded-xl border border-gray-200 bg-white shadow-md px-4 md:px-6 py-2.5 flex items-center justify-between gap-3 shrink-0">
      <div className="text-sm text-gray-500 min-w-0">
        <span className="hidden sm:inline">{section} / </span>
        <span className="text-gray-900 font-medium">{title}</span>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 min-w-0 text-xs">
        {week && (
          <span className="shrink-0 font-medium text-gray-800 tabular-nums" title="Selected week">
            {week}
          </span>
        )}
        {shortRun && (
          <span
            className="hidden md:inline truncate text-gray-500 max-w-[10rem]"
            title={runId}
          >
            {shortRun}
          </span>
        )}
        <span
          className={`shrink-0 text-[11px] font-medium px-2 py-0.5 rounded-full ${STATUS_TONE[status] || STATUS_TONE.idle}`}
        >
          {statusLabel}
        </span>
        {auth && <AuthControl auth={auth} />}
      </div>
    </header>
  )
}

TopHeader.propTypes = {
  page: PropTypes.string,
  week: PropTypes.string,
  runId: PropTypes.string,
  status: PropTypes.oneOf(['idle', 'running', 'progress', 'complete']),
  statusLabel: PropTypes.string,
  auth: PropTypes.object,
}
