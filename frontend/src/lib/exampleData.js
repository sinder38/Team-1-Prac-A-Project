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
      {
        name: 'NVIDIA Nemotron',
        consensus: 'Bearish',
        confidence: 72,
        confidenceLabel: 'High',
        spx: '-1.5% to 0.5%',
        ndx: '-2.0% to 1.0%',
        iwm: '-1.8% to 0.8%',
        evidence: 'Technical agents show mixed signals; almanac cites weak June seasonal pattern.; Macro notes high hold probability after Fed decision.',
        contradiction: 'Technical bias is bullish while almanac bias is bearish for the same week.',
        invalidation: 'A materially more dovish Fed outcome that drives yields lower would invalidate the cautious stance.',
        plainEnglish: 'Expect a cautious, range-bound week with downside skew unless the Fed surprises dovish.',
      },
      {
        name: 'Tencent HY3',
        consensus: 'Neutral-Bearish',
        confidence: 65,
        confidenceLabel: 'Medium',
        spx: '-1.2% to 0.8%',
        ndx: '-1.5% to 1.2%',
        iwm: '-1.0% to 1.0%',
        evidence: 'SPX, NDX, and IWM closed mixed last week.; Technology led gains while Energy lagged.; VIX declined indicating reduced fear.',
        contradiction: 'Bullish technical momentum conflicts with bearish seasonal patterns.',
        invalidation: 'A surprisingly dovish Fed press conference driving Treasury yields lower would reverse the cautious stance.',
        plainEnglish: 'Near-term outlook stays cautious with limited upside until Fed clarity improves.',
      },
      {
        name: 'Google Gemma',
        consensus: 'Bearish',
        confidence: 70,
        confidenceLabel: 'Medium',
        spx: '-2.0% to 0.3%',
        ndx: '-2.5% to 0.8%',
        iwm: '-1.5% to 0.5%',
        evidence: 'Technicals are mixed across indexes.; Almanac signals bearish monthly bias.; Macro frames a binary-risk environment.',
        contradiction: 'Broad indices rose last week, but June is typically the weakest midterm-year month.',
        invalidation: 'A materially more dovish-than-expected Fed press conference that drives yields lower would reverse the cautious stance.',
        plainEnglish: 'Bias leans cautiously bearish with Fed event risk as the main swing factor.',
      },
      {
        name: 'Poolside Laguna',
        consensus: 'Neutral',
        confidence: 58,
        confidenceLabel: 'Low-Medium',
        spx: '-1.0% to 1.0%',
        ndx: '-1.2% to 1.5%',
        iwm: '-0.8% to 1.2%',
        evidence: 'Indexes closed near EMAs with mixed sector leadership.; Bonds firm on stable yields.; Oil and dollar send mixed macro signals.',
        contradiction: 'Rising dollar and falling oil create mixed macro signals amid a hawkish Fed stance.',
        invalidation: 'A dovish Fed surprise that sparks a risk-on rally would invalidate the neutral stance.',
        plainEnglish: 'A balanced week with no strong directional edge unless Fed communication shifts.',
      },
    ],
  },
}

export function exampleAgentOutputs(week) {
  return { week: week || EXAMPLE_CURRENT_WEEK, ...EXAMPLE_OUTPUTS }
}

const STAGE_DEFS = [
  { id: 'stage-1', name: 'Data Fetching', description: 'Collect market data (yfinance / FRED) for the week' },
  { id: 'stage-2', name: 'Multi-Agent Processing', description: 'Run the Almanac, Macro, and Technical agents' },
  { id: 'stage-3', name: 'LLM API Calls', description: 'Query the selected LLMs and build the comparison' },
  { id: 'stage-4', name: 'Previous Week Delta', description: 'Review the previous locked prediction and create a prescription' },
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
    start: ['[stage 3] querying selected LLMs...'],
    done: ['[stage 3] wrote data/llm/llm_comparison_W24.md', '[stage 3] llm calls done.'],
  },
  {
    start: ['[stage 4] comparing the previous locked prediction with completed actuals...'],
    done: ['[stage 4] delta report and next-sprint prescription ready.'],
  },
  {
    start: ['[stage 5] awaiting human score...'],
    done: ['[stage 5] human score submitted. run complete.'],
  },
]

export function stageLogs(index) {
  return STAGE_LOGS[index] || { start: [], done: [] }
}

/**
 * Build pipeline stage list.
 * Preserves timestamps from `prevStages` for already-finished stages;
 * stamps newly started/completed stages with the real current time.
 * Pass `{ stamp: false }` for saved/archive weeks (no fake demo clock).
 */
export function exampleStages(doneCount, runningIndex = -1, prevStages = null, { stamp = true } = {}) {
  const now = new Date().toISOString()
  return STAGE_DEFS.map((s, i) => {
    let status = 'idle'
    if (i < doneCount) status = 'success'
    else if (i === runningIndex) status = 'in-progress'

    const prev = prevStages?.[i]
    let timestamp = null
    if (status === 'idle') {
      timestamp = null
    } else if (prev?.status === 'success' && prev.timestamp && status === 'success') {
      timestamp = prev.timestamp
    } else if (stamp && (status === 'success' || status === 'in-progress')) {
      timestamp = now
    }

    return {
      ...s,
      status,
      timestamp,
    }
  })
}

/** Demo accuracy shown once a run completes. */
export const DEMO_FINAL_ACCURACY = 82

/** Example submitted human score (from data/human/human_score_W24.md). */
export const EXAMPLE_HUMAN_SCORE_FORM = {
  scores: { macro: 1, technical: 0, almanac: -1, aiAgreement: 1, wildCard: 1 },
  reasoning: {
    macro: 'Macro conditions improved meaningfully this week. Treasury yields edged lower, oil fell 6.25%, and the dollar weakened slightly.',
    technical: 'SPX reclaimed ground above its 21 EMA but remains below the 7,544 ATH with no clean breakout.',
    almanac: 'June remains the historically weakest month of the midterm cycle. The bounce this week does not override the seasonal bias.',
    aiAgreement: 'All four models independently returned an Uncertain or Neutral regime with Medium confidence.',
    wildCard: 'The simultaneous drop in oil (-6.25%), yields, and DXY represents a triple-loosening that none of the agents fully captured.',
  },
  humanCall: 'Neutral-Bullish',
  confidence: 'Medium',
  overrideParagraph:
    'All four AI models returned an Uncertain or Neutral regime for Week 24. Our team agrees but leans cautiously positive given the triple-loosening in oil, yields, and the dollar.',
  wildCardInsight:
    'The simultaneous easing of oil prices, Treasury yields, and the US dollar reverses last week\'s triple-tightening. Chip sector momentum was unusually strong.',
  invalidation:
    'A hawkish Fed surprise on June 18 that drives yields higher and pushes SPX below 7,017 would invalidate the Neutral-Bullish outlook.',
  evidence: { almanac: true, macro: true, technical: true, llm: true },
}

export function isExampleWeek(week) {
  return EXAMPLE_WEEKS.some(w => w.week === week)
}

/** Demo HSR with week labels adjusted (base content is W24). */
export function exampleHumanScoreFormForWeek(week) {
  const wNum = week.split('-W')[1]?.replace(/^0+/, '') || week
  const tweak = text =>
    String(text)
      .replace(/\bWeek 24\b/g, `Week ${wNum}`)
      .replace(/\bW24\b/g, week)

  return {
    ...EXAMPLE_HUMAN_SCORE_FORM,
    reasoning: Object.fromEntries(
      Object.entries(EXAMPLE_HUMAN_SCORE_FORM.reasoning).map(([k, v]) => [k, tweak(v)]),
    ),
    overrideParagraph: tweak(EXAMPLE_HUMAN_SCORE_FORM.overrideParagraph),
    wildCardInsight: tweak(EXAMPLE_HUMAN_SCORE_FORM.wildCardInsight),
    invalidation: tweak(EXAMPLE_HUMAN_SCORE_FORM.invalidation),
  }
}

/** Fresh pipeline with nothing run yet — the human runs stages one at a time. */
export function exampleIdlePipeline(week = EXAMPLE_CURRENT_WEEK, date = EXAMPLE_CURRENT_DATE, id = null) {
  return {
    id: id || null,
    isRunning: false,
    currentStage: 0,
    stages: exampleStages(0, -1),
    accuracy: 0,
    lastRun: null,
    week,
    predictionDate: date,
  }
}

/** A fully-complete pipeline, used when viewing a saved week. */
export function exampleSavedWeekPipeline(week, date, id = null) {
  return {
    id: id || null,
    isRunning: false,
    currentStage: STAGE_DEFS.length - 1,
    stages: exampleStages(STAGE_DEFS.length, -1, null, { stamp: false }),
    accuracy: DEMO_FINAL_ACCURACY,
    lastRun: null,
    week,
    predictionDate: date,
  }
}
