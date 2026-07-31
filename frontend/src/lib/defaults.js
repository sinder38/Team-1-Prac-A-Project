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
  totalAccuracy: 0,
  currentAccuracy: 0,
  rangeAccuracy: 0,
  weeklyTrend: [],
  suggestedWeights: {},
  latestDirectionAccuracy: 0,
  latestRangeAccuracy: 0,
  latestWeek: null,
  sectorCoverage: 0,
  sectorTotal: 11,
  prescription: '',
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

function emptyFinalAsset() {
  return { direction: 'FLAT', rangeLow: '', rangeHigh: '', confidence: 'MEDIUM' }
}

export const defaultFinalPredictionForm = {
  regime: '',
  assets: {
    spx: emptyFinalAsset(),
    ndx: emptyFinalAsset(),
    iwm: emptyFinalAsset(),
    gold: emptyFinalAsset(),
    wti: emptyFinalAsset(),
    yield10y: emptyFinalAsset(),
    vix: emptyFinalAsset(),
    btc: emptyFinalAsset(),
  },
  leadingSector: '',
  laggingSector: '',
  evidence1: '',
  evidence2: '',
  evidence3: '',
  contradiction: '',
  wildCard: '',
  invalidation: '',
}
