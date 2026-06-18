/**
 * Example data so reviewers can see the dashboard working without a backend.
 * TODO (backend task): delete this file once src/api/* calls the real API.
 */

export const EXAMPLE_WEEKS = [
  { week: '2026-W22', predictionDate: '2026-05-25' },
  { week: '2026-W23', predictionDate: '2026-06-01' },
  { week: '2026-W24', predictionDate: '2026-06-08' },
]

export const EXAMPLE_CURRENT_WEEK = '2026-W24'
export const EXAMPLE_CURRENT_DATE = '2026-06-08'

const ALMANAC_RAW = `Almanac Agent Output — Week of 8–12 June 2026

MONTH: June 2026
CYCLE CONTEXT: Midterm election year. Q2-Q3 remains the Almanac "Weak Spot" before the stronger Q4 period.

MONTHLY STATS:
- S&P 500: ranks #9 of 12 months. Midterm June avg -2.1%.
- Nasdaq: ranks #9 of 12 months. Avg +1.0% normally.

ALMANAC SEASONAL BIAS: Bearish.
PATTERN CONFIDENCE: MEDIUM. Macro events and technical levels can override seasonality.`

const MACRO_RAW = `Macro Agent Output — Week of 8 June 2026

FED & RATES:
- Current Fed rate: 3.50%-3.75%. Next FOMC June 18. Hold probability 97.4%.
- 2y 4.05% / 10y 4.45% / 30y 4.95%. 10y direction: falling.

COMMODITIES & DOLLAR:
- WTI Crude Oil: 84.88, weekly change -6.25%.
- Gold: 4238.8, weekly change -2.27%.
- DXY: 99.75, weekly change -0.32%.

MACRO BIAS: Binary-risk.
CONFIDENCE: Medium.`

const TECHNICAL_RAW = `Technical Agent Output — Week of 8 June 2026

INSTRUMENT: S&P 500 (SPX), Daily Chart
LAST CLOSE: 7,554 (Fri 5 Jun 2026)

8 EMA vs PRICE: price ABOVE the 8 EMA (~7,450).
8 EMA vs 21 EMA: 8 EMA ABOVE 21 EMA (~7,432).
EMA condition: Zone 1 (Bullish) — price above both EMAs.
TRENDLINE: range 7,238-7,432. Price above support.

TECHNICAL BIAS: Bullish.
CONFIDENCE: Medium.
INVALIDATION: Close below 7,238.`

const EXAMPLE_OUTPUTS = {
  almanac: {
    agent: 'Almanac Agent',
    metrics: [
      { label: 'Month', value: 'June 2026' },
      { label: 'Cycle Context', value: 'Midterm election year — Q2-Q3 Almanac "Weak Spot".' },
      { label: 'S&P 500', value: 'Ranks #9 of 12 months. Midterm June avg -2.1%.' },
      { label: 'Nasdaq', value: 'Ranks #9 of 12 months. Avg +1.0% normally.' },
    ],
    rawData: ALMANAC_RAW,
  },
  macro: {
    agent: 'Macro Agent',
    metrics: [
      { label: 'Fed Rate', value: '3.50%-3.75% (hold 97.4%)' },
      { label: '10Y Yield', value: '4.450% — falling' },
      { label: 'WTI Crude', value: '84.88 (-6.25% w/w)' },
      { label: 'Gold', value: '4,238.8 (-2.27% w/w)' },
    ],
    rawData: MACRO_RAW,
  },
  technical: {
    agent: 'Technical Agent',
    metrics: [
      { label: 'Instrument', value: 'S&P 500 (SPX), Daily Chart' },
      { label: 'Last Close', value: '7,554 (Fri 5 Jun 2026)' },
      { label: 'EMA Condition', value: 'Zone 1 (Bullish) — price above both EMAs.' },
      { label: 'Trendline', value: 'Range 7,238-7,432. Price above support.' },
    ],
    rawData: TECHNICAL_RAW,
  },
  llmComparison: {
    finalConsensus: 'Neutral-Bearish',
    disagreementRatio: 25,
    models: [
      { name: 'NVIDIA Nemotron', consensus: 'Bearish', confidence: 72 },
      { name: 'OpenAI gpt-oss', consensus: 'Neutral-Bearish', confidence: 65 },
      { name: 'Google Gemma', consensus: 'Bearish', confidence: 70 },
      { name: 'Poolside Laguna', consensus: 'Neutral', confidence: 58 },
    ],
  },
}

export function exampleAgentOutputs(week) {
  return { week: week || EXAMPLE_CURRENT_WEEK, ...EXAMPLE_OUTPUTS }
}

export const EXAMPLE_CALIBRATION = {
  currentAccuracy: 78,
  targetAccuracy: 85,
  weeklyTrend: [64, 71, 69, 78],
  agentAccuracies: { almanac: 74, macro: 71, technical: 82 },
  lastCalculated: '2026-06-08T14:30:00Z',
}

const STAGE_DEFS = [
  { id: 'stage-1', name: 'Data Fetching', description: 'Collect market data (yfinance / FRED) for the week' },
  { id: 'stage-2', name: 'Multi-Agent Processing', description: 'Run the Almanac, Macro, and Technical agents' },
  { id: 'stage-3', name: 'LLM API Calls', description: 'Query the 4 LLMs and build the comparison' },
  { id: 'stage-4', name: 'Delta Calibration Engine', description: 'Compare predictions and calculate deltas' },
  { id: 'stage-5', name: 'Human Score', description: 'Fill in and submit the human score report' },
]

/** Log lines emitted when each stage starts and finishes (by stage index). */
export const STAGE_LOGS = [
  {
    start: ['[stage 1] fetching market data (yfinance / FRED)...'],
    done: ['[stage 1] SPX/NDX/IWM + macro series loaded.', '[stage 1] data fetching done.'],
  },
  {
    start: [
      '[stage 2] running almanac...',
      '[stage 2] running technical...',
      '[stage 2] running macro...',
    ],
    done: ['[stage 2] almanac / technical / macro complete.'],
  },
  {
    start: ['[stage 3] querying llm:nemotron, gptoss, gemma, laguna...'],
    done: ['[stage 3] wrote data/llm/llm_comparison_W24.md', '[stage 3] llm calls done.'],
  },
  {
    start: ['[stage 4] calibrating deltas vs LLM consensus...'],
    done: ['[stage 4] calibration done.'],
  },
  {
    start: ['[stage 5] awaiting human score...'],
    done: ['[stage 5] human score submitted. run complete.'],
  },
]

/** Flat log list (used for the historical/saved-week view). */
export const EXAMPLE_LOGS = STAGE_LOGS.flatMap(s => [...s.start, ...s.done])

export function stageLogs(index) {
  return STAGE_LOGS[index] || { start: [], done: [] }
}

/**
 * Build a pipeline state with the first `doneCount` stages successful.
 * `runningIndex` (optional) marks one stage as in-progress.
 */
export function exampleStages(doneCount, runningIndex = -1) {
  return STAGE_DEFS.map((s, i) => {
    let status = 'idle'
    if (i < doneCount) status = 'success'
    else if (i === runningIndex) status = 'in-progress'
    return {
      ...s,
      status,
      progress: status === 'success' ? 100 : status === 'in-progress' ? 50 : 0,
      timestamp: status === 'idle' ? null : '2026-06-08T14:30:00Z',
      errorMessage: null,
    }
  })
}

export function exampleCompletedPipeline() {
  return {
    id: 'pipeline-demo',
    isRunning: false,
    startTime: null,
    currentStage: 4,
    stages: exampleStages(5),
    accuracy: 82,
    lastRun: '2026-06-08T14:30:00Z',
    week: EXAMPLE_CURRENT_WEEK,
    predictionDate: EXAMPLE_CURRENT_DATE,
  }
}

/** Fresh pipeline with nothing run yet — the human runs stages one at a time. */
export function exampleIdlePipeline(week = EXAMPLE_CURRENT_WEEK, date = EXAMPLE_CURRENT_DATE) {
  return {
    id: 'pipeline-demo',
    isRunning: false,
    startTime: null,
    currentStage: 0,
    stages: exampleStages(0, -1),
    accuracy: 0,
    lastRun: null,
    week,
    predictionDate: date,
  }
}
