/**
 * Final consensus brief form — same submit/copy flow as Human Score.
 * Layout follows data/final prediction/prediction_*_Team1.md.
 */
import { useState } from 'react'
import PropTypes from 'prop-types'
import { AlertCircle, Send, Copy, Check } from 'lucide-react'
import { defaultFinalPredictionForm } from '../../lib/defaults'
import {
  FINAL_PRED_ASSETS,
  FINAL_PRED_DIRECTIONS,
  FINAL_PRED_CONFIDENCE,
} from '../../lib/constants'
import {
  buildFinalPredictionMarkdown,
  formatAssetRange,
  isFinalPredictionComplete,
} from '../../lib/finalPrediction'

function Section({ title, children }) {
  return (
    <div className="border-t border-gray-100 pt-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">{title}</p>
      {children}
    </div>
  )
}

function rangeFieldLabels(kind) {
  if (kind === 'level') return { low: 'Low', high: 'High', hint: 'level' }
  if (kind === 'yield') return { low: 'Low %', high: 'High %', hint: 'yield' }
  return { low: 'Low %', high: 'High %', hint: 'move' }
}

const inputClass =
  'mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:border-gray-400'
const areaClass = `${inputClass} resize-none`

export default function FinalPredictionForm({
  week = '—',
  predictionDate,
  hsrReady = false,
  onComplete,
}) {
  const [form, setForm] = useState(defaultFinalPredictionForm)
  const [status, setStatus] = useState(null)
  const [copied, setCopied] = useState(false)

  function setField(key, value) {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  function setAsset(key, field, value) {
    setForm(prev => ({
      ...prev,
      assets: {
        ...prev.assets,
        [key]: { ...prev.assets[key], [field]: value },
      },
    }))
  }

  const canSubmit = hsrReady && isFinalPredictionComplete(form)

  async function submit() {
    if (!canSubmit) return
    try {
      await onComplete?.(form)
      setStatus('ok')
    } catch {
      setStatus('fail')
    }
    setTimeout(() => setStatus(null), 2500)
  }

  async function copyMarkdown() {
    const md = buildFinalPredictionMarkdown(form, { week, filedDate: predictionDate })
    try {
      await navigator.clipboard.writeText(md)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="w-full">
      <div className="bg-white border border-gray-200 rounded-lg shadow-md">
        <div className="px-6 py-5 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">
            Final Prediction — {week}
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Team consensus brief (locked prediction for the week)
          </p>
          {!hsrReady && (
            <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
              Submit the Human Score Report first, then file this brief.
            </p>
          )}
        </div>

        <div className="px-6 py-5 space-y-5">
          <Section title="Regime">
            <textarea
              value={form.regime}
              onChange={e => setField('regime', e.target.value)}
              placeholder="e.g. Bearish with medium uncertainty. …"
              className={`${areaClass} h-28`}
            />
          </Section>

          <Section title="Asset calls">
            <div className="space-y-3">
              {FINAL_PRED_ASSETS.map(asset => {
                const row = form.assets[asset.key]
                const labels = rangeFieldLabels(asset.rangeKind)
                const preview = formatAssetRange(asset.key, row)
                return (
                  <div key={asset.key} className="border border-gray-100 rounded-md p-3">
                    <p className="text-sm font-medium text-gray-900 mb-2">{asset.label}</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                      <div>
                        <label className="text-xs font-medium text-gray-500">Direction</label>
                        <select
                          value={row.direction}
                          onChange={e => setAsset(asset.key, 'direction', e.target.value)}
                          className={inputClass}
                        >
                          {FINAL_PRED_DIRECTIONS.map(d => (
                            <option key={d}>{d}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500">{labels.low}</label>
                        <input
                          type="number"
                          step={asset.step}
                          value={row.rangeLow}
                          onChange={e => setAsset(asset.key, 'rangeLow', e.target.value)}
                          placeholder={asset.rangeKind === 'level' ? '17' : asset.rangeKind === 'yield' ? '4.50' : '-2.5'}
                          className={inputClass}
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500">{labels.high}</label>
                        <input
                          type="number"
                          step={asset.step}
                          value={row.rangeHigh}
                          onChange={e => setAsset(asset.key, 'rangeHigh', e.target.value)}
                          placeholder={asset.rangeKind === 'level' ? '28' : asset.rangeKind === 'yield' ? '4.75' : '0.5'}
                          className={inputClass}
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500">Confidence</label>
                        <select
                          value={row.confidence}
                          onChange={e => setAsset(asset.key, 'confidence', e.target.value)}
                          className={inputClass}
                        >
                          {FINAL_PRED_CONFIDENCE.map(c => (
                            <option key={c}>{c}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    {preview ? (
                      <p className="mt-2 text-xs text-gray-500">
                        Range: <span className="font-medium text-gray-700">{preview}</span>
                      </p>
                    ) : (
                      <p className="mt-2 text-xs text-gray-400">
                        Enter low and high {labels.hint} — formats itself for the brief.
                      </p>
                    )}
                  </div>
                )
              })}
            </div>
          </Section>

          <Section title="Leading sector">
            <textarea
              value={form.leadingSector}
              onChange={e => setField('leadingSector', e.target.value)}
              placeholder="**Energy (XLE)** — …"
              className={`${areaClass} h-24`}
            />
          </Section>

          <Section title="Lagging sector">
            <textarea
              value={form.laggingSector}
              onChange={e => setField('laggingSector', e.target.value)}
              placeholder="**Technology (XLK)** — …"
              className={`${areaClass} h-24`}
            />
          </Section>

          <Section title="Key evidence (3 points)">
            {[1, 2, 3].map(n => (
              <textarea
                key={n}
                value={form[`evidence${n}`]}
                onChange={e => setField(`evidence${n}`, e.target.value)}
                placeholder={`Point ${n}…`}
                className={`${areaClass} h-20 ${n > 1 ? 'mt-2' : ''}`}
              />
            ))}
          </Section>

          <Section title="Key contradiction">
            <textarea
              value={form.contradiction}
              onChange={e => setField('contradiction', e.target.value)}
              placeholder="Why confidence is Medium, not High…"
              className={`${areaClass} h-28`}
            />
          </Section>

          <Section title="Human override / wild card">
            <textarea
              value={form.wildCard}
              onChange={e => setField('wildCard', e.target.value)}
              placeholder="Team counterweight the models do not fully price in…"
              className={`${areaClass} h-28`}
            />
          </Section>

          <Section title="Invalidation conditions">
            <textarea
              value={form.invalidation}
              onChange={e => setField('invalidation', e.target.value)}
              placeholder="Our thesis is wrong if: (a) … (b) …"
              className={`${areaClass} h-32`}
            />
          </Section>
        </div>

        <div className="px-6 py-4 border-t border-gray-100 flex flex-col sm:flex-row gap-3">
          <button
            type="button"
            onClick={submit}
            disabled={!canSubmit}
            title={
              !hsrReady
                ? 'Submit Human Score first'
                : !isFinalPredictionComplete(form)
                  ? 'Fill regime and SPX / NDX / IWM ranges'
                  : undefined
            }
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" /> Submit Final Prediction
          </button>
          <button
            type="button"
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

FinalPredictionForm.propTypes = {
  week: PropTypes.string,
  predictionDate: PropTypes.string,
  hsrReady: PropTypes.bool,
  onComplete: PropTypes.func,
}
