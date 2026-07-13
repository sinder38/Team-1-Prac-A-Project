/**
 * Saved runs and agent outputs, read from the Flask backend's /artifacts/* routes.
 */
import { getJson } from './http'
import { DEFAULT_HORIZON_DAYS, LLM_MODELS } from './pipeline'

const CONFIDENCE_SCORE = { Low: 40, 'Low-Medium': 55, Medium: 65, High: 85 }

function almanacCard(a) {
  return {
    agent: 'Almanac Agent',
    metrics: [
      { label: 'Monthly Bias', value: a.monthly_bias },
      { label: 'Seasonal Bias', value: a.seasonal_bias },
      { label: 'Thesis', value: a.thesis },
      ...(a.weekly_pattern ? [{ label: 'Weekly Pattern', value: a.weekly_pattern }] : []),
    ],
    rawData: [
      `Almanac Agent Output — ${a.prediction_date}`,
      '',
      a.thesis,
      '',
      `ALMANAC SEASONAL BIAS: ${a.seasonal_bias}.`,
      `PATTERN CONFIDENCE: ${String(a.confidence).toUpperCase()}.`,
    ].join('\n'),
  }
}

function technicalCard(t) {
  const inst = t.instruments?.SPX || Object.values(t.instruments || {})[0] || {}
  return {
    agent: 'Technical Agent',
    metrics: [
      { label: 'Instrument', value: 'S&P 500 (SPX)' },
      { label: 'Last Close', value: String(inst.last_close) },
      { label: 'EMA (8/21)', value: `${inst.ema_8} / ${inst.ema_21}` },
      { label: 'Support / Resistance', value: `${inst.key_support} - ${inst.key_resistance}` },
    ],
    rawData: [
      'Technical Agent Output',
      '',
      'INSTRUMENT: S&P 500 (SPX)',
      `LAST CLOSE: ${inst.last_close}`,
      '',
      `TECHNICAL BIAS: ${inst.trend_bias}.`,
      `CONFIDENCE: ${inst.confidence}.`,
    ].join('\n'),
  }
}

function macroCard(m) {
  return {
    agent: 'Macro Agent',
    metrics: [
      { label: 'Fed Rate', value: m.fed_rate },
      { label: '10Y Yield', value: `${m.yield_10y}% — ${m.yield_10y_direction}` },
      { label: 'WTI Crude', value: `${m.wti_oil?.price} (${m.wti_oil?.weekly_change}% w/w)` },
      { label: 'Gold', value: `${m.gold?.price} (${m.gold?.weekly_change}% w/w)` },
    ],
    rawData: [
      'Macro Agent Output',
      '',
      m.primary_driver,
      '',
      `MACRO BIAS: ${m.macro_bias}.`,
      `CONFIDENCE: ${m.confidence}.`,
    ].join('\n'),
  }
}

function buildLlmComparison(models) {
  const counts = {}
  for (const { data } of models) {
    counts[data.weekly_regime] = (counts[data.weekly_regime] || 0) + 1
  }
  const finalConsensus = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'Uncertain'
  const agreeing = counts[finalConsensus] || 0
  const disagreementRatio = models.length
    ? Math.round(((models.length - agreeing) / models.length) * 100)
    : 0

  return {
    finalConsensus,
    disagreementRatio,
    models: models.map(({ name, data }) => ({
      name,
      consensus: data.weekly_regime,
      confidence: CONFIDENCE_SCORE[data.confidence] ?? 50,
    })),
  }
}

/**
 * List saved runs for the week containing `predictionDate` (there is no cross-week
 * index). The week picker keys entries by week label alone, so only the most
 * recent run_id per week is kept.
 */
export async function getAvailableWeeks(predictionDate) {
  if (!predictionDate) return { weeks: [] }
  const data = await getJson(`/artifacts/runs?prediction_date=${predictionDate}`)
  const runIds = data.run_ids || []
  if (!runIds.length) return { weeks: [] }
  return {
    weeks: [{ week: data.week, predictionDate, runId: runIds[runIds.length - 1] }],
  }
}

export async function getAgentOutputs({
  predictionDate,
  runId,
  horizonDays = DEFAULT_HORIZON_DAYS,
  includeLlm = true,
}) {
  const qs = `prediction_date=${predictionDate}&run_id=${runId}&horizon_days=${horizonDays}`

  const [almanac, technical, macro] = await Promise.all([
    getJson(`/artifacts/almanac?${qs}`),
    getJson(`/artifacts/technical?${qs}`),
    getJson(`/artifacts/macro?${qs}`),
  ])

  let llmComparison = null
  if (includeLlm) {
    try {
      const models = await Promise.all(
        LLM_MODELS.map(({ key, name }) =>
          getJson(`/artifacts/llm?${qs}&model=${key}`).then(data => ({ name, data })),
        ),
      )
      llmComparison = buildLlmComparison(models)
    } catch {
      llmComparison = null
    }
  }

  return {
    almanac: almanacCard(almanac),
    technical: technicalCard(technical),
    macro: macroCard(macro),
    llmComparison,
  }
}
