/**
 * Market-direction classification, extracted so it can be unit-tested and shared
 * (agent cards + human-score report both derive direction from free text).
 *
 * Agents/LLMs emit free-form labels like "Bullish", "Neutral-Bearish", or a
 * whole sentence. We reduce that to one of three directions. "neutral" wins only
 * when neither bull nor bear is present, or when both appear (genuinely mixed).
 */
export const DIRECTIONS = Object.freeze({
  BULLISH: 'bullish',
  BEARISH: 'bearish',
  NEUTRAL: 'neutral',
})

export function classifyBias(text) {
  const t = String(text ?? '').toLowerCase()
  const bull = t.includes('bull')
  const bear = t.includes('bear')
  if (bull && !bear) return DIRECTIONS.BULLISH
  if (bear && !bull) return DIRECTIONS.BEARISH
  return DIRECTIONS.NEUTRAL
}

/** Human-readable direction label, e.g. "Bullish". */
export function directionLabel(direction) {
  if (direction === DIRECTIONS.BULLISH) return 'Bullish'
  if (direction === DIRECTIONS.BEARISH) return 'Bearish'
  return 'Mixed'
}

/**
 * Summarise how many models agree with the consensus direction, e.g.
 * "3 of 4 models bearish". Returns an em dash when there are no models.
 */
export function summarizeModelAgreement(llm) {
  const models = Array.isArray(llm?.models) ? llm.models : []
  if (models.length === 0) return '—'

  const direction = classifyBias(llm?.finalConsensus)
  const matching = models.filter(m => classifyBias(m?.consensus) === direction).length
  return `${matching} of ${models.length} models ${directionLabel(direction).toLowerCase()}`
}
