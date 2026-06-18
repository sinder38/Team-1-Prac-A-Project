/**
 * Shows LLM results side by side and the overall agreement.
 */
export default function LlmComparisonPanel({ comparison, expanded, onToggle }) {
  if (!comparison) return null

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-gray-900">LLM Consensus</p>
          <p className="text-lg font-semibold text-gray-900 mt-0.5">
            {comparison.finalConsensus}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-xs text-gray-500">Agreement</p>
            <p className="text-sm font-semibold">
              {100 - comparison.disagreementRatio}%
            </p>
          </div>
          <button
            onClick={onToggle}
            className="px-3 py-1.5 text-xs border border-gray-200 rounded-md hover:bg-gray-50 text-gray-600"
          >
            {expanded ? 'Hide' : 'Models'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-3 gap-2">
          {comparison.models.map(m => (
            <div key={m.name} className="px-3 py-2 bg-gray-50 rounded-md text-xs">
              <p className="font-medium text-gray-900">{m.name}</p>
              <p className="text-gray-600 mt-0.5">{m.consensus} · {m.confidence}%</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
