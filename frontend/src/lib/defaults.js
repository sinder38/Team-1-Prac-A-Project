/**
 * Empty default data shapes. Backend responses should look like this.
 */
export const emptyAgentOutputs = {
  almanac: null,
  macro: null,
  technical: null,
  llmComparison: null,
}

export const defaultCalibration = {
  currentAccuracy: 0,
  targetAccuracy: 85,
  weeklyTrend: [],
  agentAccuracies: { almanac: 0, macro: 0, technical: 0 },
  lastCalculated: null,
}

export const defaultReviewForm = {
  scores: { macro: 0, technical: 0, almanac: 0, aiAgreement: 0, wildCard: 0 },
  reasoning: { macro: '', technical: '', almanac: '', aiAgreement: '', wildCard: '' },
  humanCall: 'Neutral',
  confidence: 'Medium',
  overrideParagraph: '',
  wildCardInsight: '',
  invalidation: '',
  evidence: { almanac: true, macro: true, technical: true, llm: true },
}
