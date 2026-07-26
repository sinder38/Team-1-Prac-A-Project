/**
 * Shows LLM consensus plus a side-by-side comparison of each model's full response.
 */
import PropTypes from 'prop-types'

const DIMENSIONS = [
  { key: 'consensus', label: 'Weekly Regime' },
  { key: 'confidenceLabel', label: 'Confidence', fallback: m => (m.confidence != null ? `${m.confidence}%` : '—') },
  { key: 'spx', label: 'SPX % estimate' },
  { key: 'ndx', label: 'NDX % estimate' },
  { key: 'iwm', label: 'IWM % estimate' },
  { key: 'evidence', label: 'Top supporting reason' },
  { key: 'contradiction', label: 'Top contradiction' },
  { key: 'invalidation', label: 'Invalidation condition' },
  { key: 'plainEnglish', label: 'Plain-English summary' },
]

function cellValue(model, dim) {
  const raw = model[dim.key]
  if (raw != null && raw !== '') return raw
  if (dim.fallback) return dim.fallback(model)
  return '—'
}

const EMPTY_CELLS = new Set(['', '—', '-', '–', 'n/a', 'na'])

const MODEL_OUTPUT_FIELDS = [
  'consensus',
  'spx',
  'ndx',
  'iwm',
  'evidence',
  'contradiction',
  'invalidation',
  'plainEnglish',
]

/** Drop unused/failed model columns (all dashes), e.g. gpt-oss left in an old table. */
function modelHasOutput(model) {
  return MODEL_OUTPUT_FIELDS.some(key => {
    const v = String(model?.[key] ?? '').trim().toLowerCase()
    return v && !EMPTY_CELLS.has(v)
  })
}

export default function LlmComparisonPanel({ comparison, expanded, onToggle }) {
  if (!comparison) return null

  const models = (Array.isArray(comparison.models) ? comparison.models : []).filter(modelHasOutput)
  const agreement = Number.isFinite(comparison.disagreementRatio)
    ? `${100 - comparison.disagreementRatio}%`
    : '—'

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-md p-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-gray-900">LLM Consensus</p>
          <p className="text-lg font-semibold text-gray-900 mt-0.5">
            {comparison.finalConsensus || '—'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-xs text-gray-500">Agreement</p>
            <p className="text-sm font-semibold">{agreement}</p>
          </div>
          <button
            onClick={onToggle}
            className="px-3 py-1.5 text-xs border border-gray-200 rounded-md hover:bg-gray-50 text-gray-600"
          >
            {expanded ? 'Hide' : 'Details'}
          </button>
        </div>
      </div>

      {expanded && models.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            {models.map(m => (
              <div key={m.name} className="px-3 py-2 bg-gray-50 rounded-md text-xs">
                <p className="font-medium text-gray-900">{m.name}</p>
                <p className="text-gray-600 mt-0.5">
                  {m.consensus} · {m.confidenceLabel || `${m.confidence}%`}
                </p>
              </div>
            ))}
          </div>

          <div className="overflow-x-auto rounded-md border border-gray-200">
            <table className="min-w-full text-left text-xs">
              <thead className="bg-gray-50 text-gray-500">
                <tr>
                  <th className="sticky left-0 z-10 bg-gray-50 px-3 py-2 font-medium min-w-[9rem]">
                    Dimension
                  </th>
                  {models.map(m => (
                    <th key={m.name} className="px-3 py-2 font-medium min-w-[14rem] text-gray-700">
                      {m.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {DIMENSIONS.map(dim => (
                  <tr key={dim.key} className="align-top">
                    <th className="sticky left-0 z-10 bg-white px-3 py-2.5 font-semibold text-gray-800 whitespace-nowrap">
                      {dim.label}
                    </th>
                    {models.map(m => (
                      <td key={`${m.name}-${dim.key}`} className="px-3 py-2.5 text-gray-700 leading-relaxed">
                        {cellValue(m, dim)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

LlmComparisonPanel.propTypes = {
  comparison: PropTypes.shape({
    finalConsensus: PropTypes.string,
    disagreementRatio: PropTypes.number,
    models: PropTypes.array,
  }),
  expanded: PropTypes.bool,
  onToggle: PropTypes.func,
}
