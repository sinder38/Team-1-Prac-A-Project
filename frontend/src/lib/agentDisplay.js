/**
 * Turn raw agent API data into clean card content (bias, metrics, highlight tokens).
 */
import { classifyBias, DIRECTIONS } from './bias'

const MAX_VALUE = 220
const MAX_METRICS = 10
const SKIP_LABELS = /^quick note$/i

const BIAS_PATTERNS = {
  almanac: /ALMANAC SEASONAL BIAS:\s*(.+)/i,
  macro: /MACRO BIAS:\s*(.+)/i,
  technical: /TECHNICAL BIAS:\s*(.+)/i,
}

const CONFIDENCE_PATTERNS = {
  almanac: /PATTERN CONFIDENCE:\s*(\w+)/i,
  macro: /CONFIDENCE:\s*(\w+)/i,
  technical: /CONFIDENCE:\s*(\w+)/i,
}

// Raw-output only: percentages + direction words (no tickers / confidence levels).
const HIGHLIGHT_RE =
  /(\b\d+(?:\.\d+)?%|[+-]\d+(?:\.\d+)?%|\b(?:Bullish|Bearish|Neutral|Hawkish|Dovish|Mixed|Binary[- ]risk)\b)/gi

function trimValue(text) {
  const value = String(text ?? '').trim()
  if (value.length <= MAX_VALUE) return value
  return `${value.slice(0, MAX_VALUE - 1)}…`
}

function tokenKind(token) {
  if (/%/.test(token)) return 'pct'
  if (/^(Bullish|Bearish|Neutral|Hawkish|Dovish|Mixed|Binary)/i.test(token)) return 'bias'
  return 'text'
}

/** Split raw agent text into { kind, text } segments for light highlighting. */
export function tokenizeHighlight(text) {
  const src = String(text ?? '')
  if (!src) return []
  return src.split(HIGHLIGHT_RE).filter(Boolean).map(part => ({
    kind: tokenKind(part),
    text: part,
  }))
}

export function biasBadgeClass(tone) {
  if (tone === DIRECTIONS.BULLISH) return 'bg-emerald-50 text-emerald-700 ring-emerald-600/20'
  if (tone === DIRECTIONS.BEARISH) return 'bg-red-50 text-red-700 ring-red-600/20'
  return 'bg-amber-50 text-amber-800 ring-amber-600/20'
}

export function prepareAgentCard(id, data) {
  if (!data) return null

  const raw = data.rawData || ''
  const biasMatch = raw.match(BIAS_PATTERNS[id])
  const confMatch = raw.match(CONFIDENCE_PATTERNS[id])
  const bias = biasMatch ? biasMatch[1].replace(/\.$/, '').trim() : null
  const confidence = confMatch ? confMatch[1].trim() : null

  const metrics = (data.metrics || [])
    .filter(m => m?.label && m?.value != null && String(m.value).trim() !== '')
    .filter(m => !SKIP_LABELS.test(String(m.label).trim()))
    .map(m => ({ label: String(m.label).trim(), value: trimValue(m.value) }))
    .slice(0, MAX_METRICS)

  const headline = metrics[0] || null
  const details = metrics.slice(1)

  return {
    name: data.agent,
    bias,
    biasTone: classifyBias(bias),
    confidence,
    headline,
    details,
    rawData: raw,
  }
}
