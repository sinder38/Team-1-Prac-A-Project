/**
 * Bias chips + bull-vs-bear conflict line for the dashboard strip.
 */
import { prepareAgentCard } from './agentDisplay'
import { classifyBias, DIRECTIONS } from './bias'

const SOURCES = [
  { id: 'almanac', label: 'Almanac' },
  { id: 'macro', label: 'Macro' },
  { id: 'technical', label: 'Technical' },
]

function shortBias(text) {
  return String(text || '')
    .split(/[.(]/)[0]
    .trim()
}

function makeSignal(id, label, text) {
  const cleaned = shortBias(text)
  if (!cleaned) return null
  return { id, label, text: cleaned, tone: classifyBias(cleaned) }
}

export function buildWeekSummary({ outputs = {}, finalPrediction = null } = {}) {
  const signals = []

  for (const { id, label } of SOURCES) {
    const s = makeSignal(id, label, prepareAgentCard(id, outputs[id])?.bias)
    if (s) signals.push(s)
  }

  const llm = makeSignal('llm', 'LLM', outputs.llmComparison?.finalConsensus)
  if (llm) signals.push(llm)

  const final = makeSignal('final', 'Final', finalPrediction?.form?.regime)
  if (final) signals.push(final)

  return {
    signals,
    conflict: findConflict(signals),
    hasSignals: signals.length > 0,
  }
}

/** @returns {string|null} e.g. "Technical Bullish vs Macro Bearish" */
export function findConflict(signals) {
  const list = Array.isArray(signals) ? signals : []
  const bulls = list.filter(s => s.tone === DIRECTIONS.BULLISH)
  const bears = list.filter(s => s.tone === DIRECTIONS.BEARISH)
  if (!bulls.length || !bears.length) return null
  const side = items => items.map(s => `${s.label} ${s.text}`).join(', ')
  return `${side(bulls)} vs ${side(bears)}`
}
