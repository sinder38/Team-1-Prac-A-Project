/**
 * Inline, dismissable error message for recoverable failures (e.g. a failed
 * data fetch). Use this instead of silently swallowing errors.
 */
import PropTypes from 'prop-types'
import { AlertCircle, RefreshCw, X } from 'lucide-react'

export default function ErrorBanner({ message, onRetry, onDismiss }) {
  if (!message) return null

  return (
    <div className="flex items-start gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
      <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
      <span className="flex-1 min-w-0">{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1 text-xs font-medium text-red-700 hover:text-red-900 shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      )}
      {onDismiss && (
        <button onClick={onDismiss} className="text-red-400 hover:text-red-700 shrink-0" aria-label="Dismiss">
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  )
}

ErrorBanner.propTypes = {
  message: PropTypes.string,
  onRetry: PropTypes.func,
  onDismiss: PropTypes.func,
}
