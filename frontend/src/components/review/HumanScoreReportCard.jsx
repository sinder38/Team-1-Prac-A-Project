/**
 * Read-only Human Score report — styled like AgentCard but larger.
 */
import { useState } from 'react'
import PropTypes from 'prop-types'
import { ClipboardCheck, ChevronDown, Copy, Check } from 'lucide-react'
import { HUMAN_DIMENSIONS, EVIDENCE_SOURCES } from '../../lib/constants'
import { buildHumanScoreMarkdown, formatSignedScore, weekTitleLabel } from '../../lib/humanScore'
import { classifyBias } from '../../lib/bias'
import { biasBadgeClass } from '../../lib/agentDisplay'

function MetricRow({ label, value, sub }) {
  return (
    <div className="py-3 border-b border-gray-100 last:border-0">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</p>
      <p className="text-base text-gray-900 mt-1 leading-snug">{value}</p>
      {sub && <p className="text-sm text-gray-500 mt-1 leading-relaxed">{sub}</p>}
    </div>
  )
}

MetricRow.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.node,
  sub: PropTypes.string,
}

export default function HumanScoreReportCard({ report }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  if (!report?.form) return null

  const { form, week, consensus, aiSaid, total, llmComparison } = report
  const totalLabel = total > 0 ? `+${total}` : `${total}`
  const callTone = classifyBias(form.humanCall)
  const evidence = EVIDENCE_SOURCES.filter(s => form.evidence?.[s.key]).map(s => s.label)
  const mdCtx = { week, consensus, aiSaid, total, llmComparison }

  async function copyMarkdown() {
    const md = report.rawMarkdown || buildHumanScoreMarkdown(form, mdCtx)
    try {
      await navigator.clipboard.writeText(md)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-md overflow-hidden hover:border-gray-300 transition-colors">
      <div className="px-6 py-4 border-b border-gray-100 bg-violet-50/80">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 rounded-lg shrink-0 bg-violet-100 text-violet-700">
              <ClipboardCheck className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h4 className="text-lg font-semibold text-gray-900 truncate">
                Human Score Analyst Output — {weekTitleLabel(week)}
              </h4>
              <p className="text-sm text-gray-500 mt-0.5">
                Confidence · {form.confidence}
              </p>
            </div>
          </div>
          {form.humanCall && (
            <span
              className={`shrink-0 text-xs font-semibold uppercase tracking-wide px-2.5 py-1 rounded-full ring-1 ${biasBadgeClass(callTone)}`}
            >
              {form.humanCall}
            </span>
          )}
        </div>
      </div>

      <div className="px-6 py-2">
        <div className="py-4 border-b border-gray-100">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
            Human Score Total
          </p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{totalLabel}</p>
        </div>

        <MetricRow label="AI Consensus" value={consensus} />

        <div className="py-4 border-b border-gray-100">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-400 mb-3">
            Score by Dimension
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {HUMAN_DIMENSIONS.map(d => (
              <div key={d.key} className="rounded-lg border border-gray-100 p-3 bg-gray-50/40">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium text-gray-900">{d.label}</p>
                  <span className="text-sm font-bold text-gray-900 shrink-0">
                    {formatSignedScore(form.scores[d.key])}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  AI said: {aiSaid[d.key] ?? '—'}
                </p>
                {form.reasoning[d.key] && (
                  <p className="text-sm text-gray-600 mt-2 leading-relaxed line-clamp-3">
                    {form.reasoning[d.key]}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {form.overrideParagraph && (
          <MetricRow label="Override Paragraph" value={form.overrideParagraph} />
        )}
        {form.wildCardInsight && (
          <MetricRow label="Wild Card Insight" value={form.wildCardInsight} />
        )}
        {form.invalidation && (
          <MetricRow label="Invalidation Condition" value={form.invalidation} />
        )}
        {evidence.length > 0 && (
          <MetricRow label="Evidence Used" value={evidence.join(' · ')} />
        )}
      </div>

      <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <button
          type="button"
          onClick={() => setOpen(v => !v)}
          className="flex items-center gap-1 text-sm font-medium text-gray-500 hover:text-gray-800"
        >
          {open ? 'Hide full report' : 'View full report'}
          <ChevronDown className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} />
        </button>
        <button
          type="button"
          onClick={copyMarkdown}
          className="flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium border border-gray-200 text-gray-700 hover:bg-white"
        >
          {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
          {copied ? 'Copied' : 'Copy as Markdown'}
        </button>
      </div>

      {open && (
        <div className="px-6 pb-5">
          <pre className="p-4 bg-white border border-gray-200 rounded-lg text-xs leading-relaxed text-gray-600 overflow-auto max-h-96 whitespace-pre-wrap">
            {report.rawMarkdown || buildHumanScoreMarkdown(form, mdCtx)}
          </pre>
        </div>
      )}
    </div>
  )
}

HumanScoreReportCard.propTypes = {
  report: PropTypes.shape({
    form: PropTypes.object.isRequired,
    week: PropTypes.string,
    consensus: PropTypes.string,
    aiSaid: PropTypes.object,
    total: PropTypes.number,
    llmComparison: PropTypes.object,
    rawMarkdown: PropTypes.string,
  }),
}
