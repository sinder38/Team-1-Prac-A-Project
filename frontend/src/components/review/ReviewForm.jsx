/**
 * Human Score report — a finished-report layout with blanks to fill in.
 * Modelled on data/human/human_score_W*.md. Submitting completes the final
 * pipeline stage.
 *
 * TODO (backend task): submitHumanScore() → POST /api/validation/human-score
 */
import { useState, useMemo } from 'react'
import PropTypes from 'prop-types'
import { AlertCircle, Send, Copy, Check } from 'lucide-react'
import { submitHumanScore, HUMAN_SCORE_DECISION } from '../../api'
import { defaultReviewForm } from '../../lib/defaults'
import {
  HUMAN_DIMENSIONS,
  SCORE_OPTIONS,
  HUMAN_CALLS,
  CONFIDENCE_LEVELS,
  EVIDENCE_SOURCES,
} from '../../lib/constants'
import { aiSaidFor, buildHumanScoreMarkdown, humanScoreTotal } from '../../lib/humanScore'

function Section({ title, children }) {
  return (
    <div className="border-t border-gray-100 pt-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">{title}</p>
      {children}
    </div>
  )
}

export default function ReviewForm({ outputs = {}, week = '—', aiComplete = false, onComplete }) {
  const [form, setForm] = useState(defaultReviewForm)
  const [status, setStatus] = useState(null)
  const [copied, setCopied] = useState(false)

  const aiSaid = useMemo(() => aiSaidFor(outputs), [outputs])
  const consensus = outputs.llmComparison?.finalConsensus || 'Pending — run the pipeline'
  const total = humanScoreTotal(form)

  function setScore(key, value) {
    setForm(prev => ({ ...prev, scores: { ...prev.scores, [key]: value } }))
  }
  function setReason(key, value) {
    setForm(prev => ({ ...prev, reasoning: { ...prev.reasoning, [key]: value } }))
  }
  function setField(key, value) {
    setForm(prev => ({ ...prev, [key]: value }))
  }
  function toggleEvidence(key) {
    setForm(prev => ({ ...prev, evidence: { ...prev.evidence, [key]: !prev.evidence[key] } }))
  }

  async function submit() {
    try {
      await submitHumanScore(form, HUMAN_SCORE_DECISION.SUBMITTED)
      onComplete?.(form)
    } catch {
      setStatus('fail')
    }
    setTimeout(() => setStatus(null), 2500)
  }

  async function copyMarkdown() {
    const md = buildHumanScoreMarkdown(form, { week, consensus, aiSaid, total })
    try {
      await navigator.clipboard.writeText(md)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable */
    }
  }

  const totalLabel = total > 0 ? `+${total}` : `${total}`

  return (
    <div className="max-w-3xl">
      <div className="bg-white border border-gray-200 rounded-lg shadow-md">
        {/* Report header */}
        <div className="px-6 py-5 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">Human Score Report — {week}</h3>
          <p className="text-sm text-gray-500 mt-1">
            AI Consensus: <span className="font-medium text-gray-700">{consensus}</span>
          </p>
          {!aiComplete && (
            <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
              Run all four AI stages on the Dashboard first — the AI Said column fills in as the
              pipeline progresses.
            </p>
          )}
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Score table */}
          <Section title="Human Score Table">
            <div className="space-y-3">
              {HUMAN_DIMENSIONS.map(d => (
                <div key={d.key} className="border border-gray-100 rounded-md p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900">{d.label}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        AI said: <span className="text-gray-700">{aiSaid[d.key]}</span>
                      </p>
                    </div>
                    <div className="flex gap-1 shrink-0">
                      {SCORE_OPTIONS.map(s => (
                        <button
                          key={s}
                          onClick={() => setScore(d.key, s)}
                          className={`w-8 h-8 text-xs font-semibold rounded-md border ${
                            form.scores[d.key] === s
                              ? 'bg-gray-900 border-gray-900 text-white'
                              : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'
                          }`}
                        >
                          {s > 0 ? `+${s}` : s}
                        </button>
                      ))}
                    </div>
                  </div>
                  <textarea
                    value={form.reasoning[d.key]}
                    onChange={e => setReason(d.key, e.target.value)}
                    placeholder="Team reasoning…"
                    className="mt-2 w-full h-16 px-3 py-2 text-sm border border-gray-200 rounded-md resize-none focus:outline-none focus:border-gray-400"
                  />
                </div>
              ))}
            </div>
          </Section>

          {/* Total */}
          <Section title="Human Score Total">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-gray-900">{totalLabel}</span>
              <span className="text-xs text-gray-400">(sum of the five team scores)</span>
            </div>
          </Section>

          {/* Call + confidence */}
          <Section title="Human Call & Confidence">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-gray-500">Human Call</label>
                <select
                  value={form.humanCall}
                  onChange={e => setField('humanCall', e.target.value)}
                  className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:border-gray-400"
                >
                  {HUMAN_CALLS.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500">Confidence</label>
                <select
                  value={form.confidence}
                  onChange={e => setField('confidence', e.target.value)}
                  className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:border-gray-400"
                >
                  {CONFIDENCE_LEVELS.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
            </div>
          </Section>

          {/* Paragraphs */}
          {[
            ['overrideParagraph', 'Override Paragraph', 'Summarise the team view vs. the AI consensus…'],
            ['wildCardInsight', 'Wild Card Insight', 'A factor the AI models did not fully emphasise…'],
            ['invalidation', 'Invalidation Condition', 'What would prove this call wrong…'],
          ].map(([key, title, ph]) => (
            <Section key={key} title={title}>
              <textarea
                value={form[key]}
                onChange={e => setField(key, e.target.value)}
                placeholder={ph}
                className="w-full h-24 px-3 py-2 text-sm border border-gray-200 rounded-md resize-none focus:outline-none focus:border-gray-400"
              />
            </Section>
          ))}

          {/* Evidence */}
          <Section title="Evidence Used">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {EVIDENCE_SOURCES.map(s => (
                <label
                  key={s.key}
                  className="flex items-center gap-2 px-3 py-2 border border-gray-100 rounded-md cursor-pointer hover:bg-gray-50"
                >
                  <input
                    type="checkbox"
                    checked={!!form.evidence[s.key]}
                    onChange={() => toggleEvidence(s.key)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-700">{s.label}</span>
                </label>
              ))}
            </div>
          </Section>
        </div>

        {/* Actions */}
        <div className="px-6 py-4 border-t border-gray-100 flex flex-col sm:flex-row gap-3">
          <button
            onClick={submit}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium bg-gray-900 text-white hover:bg-gray-800"
          >
            <Send className="w-4 h-4" /> Submit &amp; Complete Review
          </button>
          <button
            onClick={copyMarkdown}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium border border-gray-200 text-gray-700 hover:bg-gray-50"
          >
            {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied' : 'Copy as Markdown'}
          </button>
        </div>
      </div>

      {status === 'fail' && (
        <p className="mt-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
          <AlertCircle className="w-4 h-4" /> Submission failed.
        </p>
      )}
    </div>
  )
}

Section.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.node,
}

ReviewForm.propTypes = {
  outputs: PropTypes.object,
  week: PropTypes.string,
  aiComplete: PropTypes.bool,
  onComplete: PropTypes.func,
}
