/**
 * Read-only final prediction brief — same card pattern as Human Score.
 */
import { useState } from 'react'
import PropTypes from 'prop-types'
import { FileText, Copy, Check } from 'lucide-react'
import { FINAL_PRED_ASSETS } from '../../lib/constants'
import {
  buildFinalPredictionMarkdown,
  formatAssetRange,
  formatFiledDate,
} from '../../lib/finalPrediction'

function MetricRow({ label, value }) {
  return (
    <div className="py-3 border-b border-gray-100 last:border-0">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</p>
      <p className="text-sm text-gray-900 mt-1 leading-relaxed whitespace-pre-wrap">{value || '—'}</p>
    </div>
  )
}

MetricRow.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.node,
}

export default function FinalPredictionReportCard({ report }) {
  const [copied, setCopied] = useState(false)
  if (!report?.form) return null

  const { form, week, predictionDate } = report
  const md =
    report.markdown ||
    buildFinalPredictionMarkdown(form, { week, filedDate: predictionDate })

  async function copyMarkdown() {
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
      <div className="px-6 py-4 border-b border-gray-100 bg-sky-50/80">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg shrink-0 bg-sky-100 text-sky-700">
            <FileText className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h4 className="text-lg font-semibold text-gray-900 truncate">
              Final Prediction — {week}
            </h4>
            <p className="text-sm text-gray-500 mt-0.5">
              Filed · {formatFiledDate(predictionDate)}
            </p>
          </div>
          <button
            type="button"
            onClick={copyMarkdown}
            className="shrink-0 flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900"
          >
            {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied' : 'Copy Markdown'}
          </button>
        </div>
      </div>

      <div className="px-6 py-2">
        <MetricRow label="Regime" value={form.regime} />

        <div className="py-3 border-b border-gray-100">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-400 mb-2">
            Asset calls
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="text-xs text-gray-400">
                  <th className="py-1 pr-2 font-medium">Asset</th>
                  <th className="py-1 pr-2 font-medium">Direction</th>
                  <th className="py-1 pr-2 font-medium">Range</th>
                  <th className="py-1 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {FINAL_PRED_ASSETS.map(a => {
                  const row = form.assets?.[a.key] || {}
                  return (
                    <tr key={a.key} className="border-t border-gray-50 text-gray-800">
                      <td className="py-1.5 pr-2">{a.label}</td>
                      <td className="py-1.5 pr-2 font-medium">{row.direction || '—'}</td>
                      <td className="py-1.5 pr-2">{formatAssetRange(a.key, row) || '—'}</td>
                      <td className="py-1.5">{row.confidence || '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        <MetricRow label="Leading sector" value={form.leadingSector} />
        <MetricRow label="Lagging sector" value={form.laggingSector} />
        <MetricRow label="Key evidence 1" value={form.evidence1} />
        <MetricRow label="Key evidence 2" value={form.evidence2} />
        <MetricRow label="Key evidence 3" value={form.evidence3} />
        <MetricRow label="Key contradiction" value={form.contradiction} />
        <MetricRow label="Human override / wild card" value={form.wildCard} />
        <MetricRow label="Invalidation conditions" value={form.invalidation} />
      </div>
    </div>
  )
}

FinalPredictionReportCard.propTypes = {
  report: PropTypes.object,
}
