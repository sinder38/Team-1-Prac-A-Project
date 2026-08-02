/**
 * One card for a single agent (Almanac, Macro, or Technical).
 */
import PropTypes from 'prop-types'
import { BookOpen, TrendingUp, LineChart, ChevronDown } from 'lucide-react'
import { AGENTS } from '../../lib/constants'
import { prepareAgentCard, biasBadgeClass, tokenizeHighlight } from '../../lib/agentDisplay'

const AGENT_ID = PropTypes.oneOf(['almanac', 'macro', 'technical'])

const ICONS = {
  almanac: BookOpen,
  macro: TrendingUp,
  technical: LineChart,
}

const HEADER_BG = {
  almanac: 'bg-blue-50/80',
  macro: 'bg-amber-50/80',
  technical: 'bg-emerald-50/80',
}

const ICON_BG = {
  almanac: 'bg-blue-100 text-blue-700',
  macro: 'bg-amber-100 text-amber-700',
  technical: 'bg-emerald-100 text-emerald-700',
}

function highlightClass({ kind, text }) {
  if (kind === 'pct') {
    return String(text).trimStart().startsWith('-')
      ? 'text-red-600 font-semibold'
      : 'text-green-600 font-semibold'
  }
  if (kind === 'bias') {
    if (/bearish|hawkish/i.test(text)) return 'text-red-600 font-semibold'
    if (/bullish|dovish/i.test(text)) return 'text-green-600 font-semibold'
  }
  return undefined
}

function HighlightedRaw({ text }) {
  return tokenizeHighlight(text).map((tok, i) => (
    <span key={i} className={highlightClass(tok)}>
      {tok.text}
    </span>
  ))
}

HighlightedRaw.propTypes = {
  text: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
}

function MetricRow({ label, value }) {
  return (
    <div className="py-2 border-b border-gray-100 last:border-0">
      <p className="text-[11px] font-medium uppercase tracking-wide text-gray-400">{label}</p>
      <p className="text-sm text-gray-800 mt-0.5 leading-snug whitespace-pre-wrap break-words">
        {value}
      </p>
    </div>
  )
}

MetricRow.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
}

export function AgentCardPlaceholder({ id }) {
  const Icon = ICONS[id]
  const meta = AGENTS[id]

  return (
    <div className="h-full flex flex-col rounded-xl border border-dashed border-gray-200 bg-gray-50/50 shadow-md overflow-hidden">
      <div className={`px-4 py-3 border-b border-gray-100 ${HEADER_BG[id]}`}>
        <div className="flex items-center gap-2.5">
          <div className={`p-1.5 rounded-lg ${ICON_BG[id]}`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className="text-sm font-semibold text-gray-700">{meta.label}</span>
        </div>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-8 text-center">
        <p className="text-sm text-gray-400">No output yet</p>
        <p className="text-xs text-gray-400 mt-1 max-w-[180px]">
          Run the pipeline or pick a week with saved data
        </p>
      </div>
    </div>
  )
}

AgentCardPlaceholder.propTypes = {
  id: AGENT_ID.isRequired,
}

export default function AgentCard({ id, data, open, onToggle }) {
  const Icon = ICONS[id]
  const card = prepareAgentCard(id, data)
  if (!card) return null

  return (
    <div className="h-full flex flex-col rounded-xl border border-gray-200 bg-white shadow-md overflow-hidden hover:border-gray-300 transition-colors">
      <div className={`px-4 py-3 border-b border-gray-100 ${HEADER_BG[id]}`}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={`p-1.5 rounded-lg shrink-0 ${ICON_BG[id]}`}>
              <Icon className="w-4 h-4" />
            </div>
            <span className="text-sm font-semibold text-gray-900 truncate">{card.name}</span>
          </div>
          {card.bias && (
            <span
              className={`shrink-0 text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full ring-1 ${biasBadgeClass(card.biasTone)}`}
            >
              {card.bias.split(/[.(]/)[0].trim()}
            </span>
          )}
        </div>
        {card.confidence && (
          <p className="text-[11px] text-gray-500 mt-2 ml-9">
            Confidence · {card.confidence}
          </p>
        )}
      </div>

      <div className="flex-1 px-4 py-1 min-h-[140px] max-h-[22rem] overflow-y-auto">
        {card.headline && (
          <div className="py-3 border-b border-gray-100">
            <p className="text-[11px] font-medium uppercase tracking-wide text-gray-400">
              {card.headline.label}
            </p>
            <p className="text-base font-semibold text-gray-900 mt-0.5 leading-snug whitespace-pre-wrap break-words">
              {card.headline.value}
            </p>
          </div>
        )}
        {card.details.length > 0 && (
          <div>
            {card.details.map((m, i) => (
              <MetricRow key={`${m.label}-${i}`} label={m.label} value={m.value} />
            ))}
          </div>
        )}
      </div>

      <div className="px-4 py-3 border-t border-gray-100 mt-auto bg-gray-50/50">
        <button
          type="button"
          onClick={onToggle}
          className="flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-gray-800"
        >
          {open ? 'Hide raw output' : 'View full raw output'}
          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${open ? 'rotate-180' : ''}`} />
        </button>
        {open && (
          <pre className="mt-2 p-3 bg-white border border-gray-200 rounded-lg text-[11px] leading-relaxed text-gray-700 overflow-auto max-h-[32rem] whitespace-pre-wrap break-words font-mono">
            <HighlightedRaw text={card.rawData} />
          </pre>
        )}
      </div>
    </div>
  )
}

AgentCard.propTypes = {
  id: AGENT_ID.isRequired,
  data: PropTypes.object,
  open: PropTypes.bool,
  onToggle: PropTypes.func,
}
