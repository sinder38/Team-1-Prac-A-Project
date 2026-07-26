/**
 * Fields for the Human Score report (modelled on data/human/human_score_W*.md).
 */
export const HUMAN_DIMENSIONS = [
  { key: 'macro', label: 'Macro / News Weight' },
  { key: 'technical', label: 'Technical Structure' },
  { key: 'almanac', label: 'Almanac Seasonal Weight' },
  { key: 'aiAgreement', label: 'AI Model Agreement Quality' },
  { key: 'wildCard', label: 'Wild Card / Human Observation' },
]

export const SCORE_OPTIONS = [-2, -1, 0, 1, 2]

export const HUMAN_CALLS = [
  'Bullish',
  'Neutral-Bullish',
  'Neutral',
  'Neutral-Bearish',
  'Bearish',
]

export const CONFIDENCE_LEVELS = ['Low', 'Medium', 'High']

export const EVIDENCE_SOURCES = [
  { key: 'almanac', label: 'R3 Almanac Agent Output' },
  { key: 'macro', label: 'R4 Macro Agent Output' },
  { key: 'technical', label: 'R5 Technical Agent Output' },
  { key: 'llm', label: 'R6 LLM Comparison Output' },
]
