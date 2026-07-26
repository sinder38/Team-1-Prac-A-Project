/**
 * Saved runs and agent outputs, read from the Flask backend's /artifacts/* routes.
 */
import { getJson } from './http'
import { DEFAULT_HORIZON_DAYS, getLlmModels } from './pipeline'

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

function formatRange(range) {
  if (!range || range.low == null || range.high == null) return '—'
  return `${range.low}% to ${range.high}%`
}

function joinList(items) {
  if (!Array.isArray(items) || !items.length) return '—'
  return items.join('; ')
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
      confidenceLabel: data.confidence || '—',
      spx: formatRange(data.spx_range),
      ndx: formatRange(data.ndx_range),
      iwm: formatRange(data.iwm_range),
      evidence: joinList(data.supporting_evidence),
      contradiction: joinList(data.contradictions),
      invalidation: data.invalidation || '—',
      plainEnglish: data.plain_english || '—',
    })),
  }
}

/**
 * List all weeks that have saved pipeline runs or archive markdown on disk.
 */
export async function getAvailableWeeks() {
  const data = await getJson('/artifacts/weeks')
  const weeks = (data.weeks || []).map(w => ({
    week: w.week,
    predictionDate: w.prediction_date,
    runId: w.run_id || null,
    stem: w.stem,
    source: w.source || (w.run_id ? 'run' : 'archive'),
  }))
  return { weeks }
}

export async function getArchiveOutputs(stem) {
  const data = await getJson(`/artifacts/archive?stem=${encodeURIComponent(stem)}`)
  return {
    almanac: data.almanac || null,
    technical: data.technical || null,
    macro: data.macro || null,
    llmComparison: data.llmComparison || null,
    humanScoreReport: data.humanScoreReport || null,
  }
}

export async function getHumanScore(stem) {
  return getJson(`/artifacts/human-score?stem=${encodeURIComponent(stem)}`)
}

export async function getAgentOutputs({
  predictionDate,
  runId,
  horizonDays = DEFAULT_HORIZON_DAYS,
  includeLlm = true,
  stem,
  source,
}) {
  if (source === 'archive' || (source !== 'run' && !runId && stem)) {
    return getArchiveOutputs(stem)
  }

  const qs = `prediction_date=${predictionDate}&run_id=${runId}&horizon_days=${horizonDays}`

  const [almanac, technical, macro] = await Promise.all([
    getJson(`/artifacts/almanac?${qs}`),
    getJson(`/artifacts/technical?${qs}`),
    getJson(`/artifacts/macro?${qs}`),
  ])

  let llmComparison = null
  if (includeLlm) {
    const modelList = await getLlmModels()
    const models = []
    await Promise.all(
      modelList.map(async ({ key, name }) => {
        try {
          const data = await getJson(`/artifacts/llm?${qs}&model=${key}`)
          models.push({ name, data })
        } catch {
          // Skip models that failed or were not run.
        }
      }),
    )
    if (models.length) llmComparison = buildLlmComparison(models)
  }

  let humanScoreReport = null
  if (stem) {
    try {
      humanScoreReport = await getHumanScore(stem)
    } catch {
      // No archived human score for this week.
    }
  }

  return {
    almanac: almanacCard(almanac),
    technical: technicalCard(technical),
    macro: macroCard(macro),
    llmComparison,
    humanScoreReport,
  }
}
